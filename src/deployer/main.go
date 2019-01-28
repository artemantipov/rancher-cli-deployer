package main

import (
	"bufio"
	"database/sql"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	_ "github.com/lib/pq"
)

const (
	deployer  = iota
	stack     = iota
	service   = iota
	imageTag  = iota
	imageName = iota
)

func main() {
	gitUser := os.Getenv("GITLAB_USER_LOGIN")
	stackName := os.Args[stack]
	services := os.Args[service]
	if services == "" {
		fmt.Println("SERVICES variable required!")
		os.Exit(1)
	}
	dockerImageTag := os.Args[imageTag]
	dockerImageName := ""
	if len(os.Args) > 4 {
		dockerImageName = os.Args[imageName]
	}
	composeURI := getCompose(stackName)
	updatedURI := composeURI
	// updatedURI := fmt.Sprintf("%v/updated", composeURI)
	rancherURL := os.Getenv("RANCHER_URL")
	if strings.Contains(rancherURL, "prod.env") {
		fmt.Println("Checking user access...")
		aclCheck(gitUser, stackName)
	} else {
		fmt.Println("Check not required")
	}
	var action string
	switch services {
	case "all":
		serviceName := services
		if dockerImageTag == "rollback" {
			action = dockerImageTag
		} else {
			serviceName = "--stack"
			action = "deploy"
			composeUpdate(composeURI, updatedURI, dockerImageTag, serviceName, dockerImageName)
		}
		serviceRancher(stackName, serviceName, updatedURI, composeURI, action)
	default:
		svcList := strings.Split(services, ",")
		for _, svc := range svcList {
			serviceName := svc
			if dockerImageTag == "rollback" {
				action = dockerImageTag
				serviceRancher(stackName, serviceName, updatedURI, composeURI, action)
			} else {
				action = "deploy"
				composeUpdate(composeURI, updatedURI, dockerImageTag, serviceName, dockerImageName)
			}
		}
		serviceName := "all"
		serviceRancher(stackName, serviceName, updatedURI, composeURI, action)
	}
	defer fmt.Printf("Services: %v\nIn stack: %v\nwas updated to version: %v by user: %v\n", services, stackName, dockerImageTag, gitUser)
}

func aclCheck(user string, stackName string) bool {
	connect := os.Getenv("ACL_DB")
	db := dbConnect(connect)
	defer db.Close()
	var name, stack string
	query := fmt.Sprintf(`select name, stack from acl_view where name = '%v' and stack = '%v'`, user, stackName)
	row := db.QueryRow(query)
	err := row.Scan(&name, &stack)
	if err != nil {
		fmt.Printf("User %v doesn't have access to stack %v\n", user, stackName)
		checkFatal(err)
	}
	fmt.Printf("Found user: %v with access to stack: %v\n", name, stack)
	return true
}

func getCompose(stackName string) string {
	cmd := exec.Command("rancher", "export", stackName)
	stdoutStderr, err := cmd.CombinedOutput()
	fmt.Printf("%s\n", stdoutStderr)
	checkErr(err)
	uri := fmt.Sprintf("%v", stackName)
	return uri
}

func composeUpdate(uri string, uriUpdated string, tag string, service string, image string) {
	fmt.Println("Updating compose...")
	switch service {
	case "all":
		if image != "" {
			cmd := exec.Command("/workspace/compose_update.py", uri, uriUpdated, tag, service, "--image", image)
			stdoutStderr, err := cmd.CombinedOutput()
			fmt.Printf("%s\n", stdoutStderr)
			checkFatal(err)
		} else {
			cmd := exec.Command("/workspace/compose_update.py", uri, uriUpdated, tag, service)
			stdoutStderr, err := cmd.CombinedOutput()
			fmt.Printf("%s\n", stdoutStderr)
			checkFatal(err)
		}
	default:
		if image != "" {
			cmd := exec.Command("/workspace/compose_update.py", uri, uriUpdated, tag, "--service", service, "--image", image)
			stdoutStderr, err := cmd.CombinedOutput()
			fmt.Printf("%s\n", stdoutStderr)
			checkFatal(err)
		} else {
			cmd := exec.Command("/workspace/compose_update.py", uri, uriUpdated, tag, "--service", service)
			stdoutStderr, err := cmd.CombinedOutput()
			fmt.Printf("%s\n", stdoutStderr)
			checkFatal(err)
		}
	}

}

func serviceRancher(stackName string, serviceName string, uriUpdated string, composeURI string, action string) {
	serviceComposeParam := fmt.Sprintf("%v/docker-compose.yml", uriUpdated)
	rancherComposeParam := fmt.Sprintf("%v/rancher-compose.yml", composeURI)
	cmd := exec.Command("rancher")
	switch action {
	case "deploy":
		cmd = exec.Command("rancher", "--debug", "--wait-state", "healthy", "up", "--upgrade", "--batch-size", "1", "--pull", "--stack", stackName, "--file", serviceComposeParam, "--rancher-file", rancherComposeParam, "-d")
	case "rollback":
		if serviceName == "all" {
			cmd = exec.Command("rancher", "--debug", "--wait-state", "healthy", "up", "--stack", stackName, "--file", serviceComposeParam, "--rancher-file", rancherComposeParam, "-d", "--rollback")
		} else {
			cmd = exec.Command("rancher", "--debug", "--wait-state", "healthy", "up", "--stack", stackName, "--file", serviceComposeParam, "--rancher-file", rancherComposeParam, "-d", "--rollback", serviceName)
		}
	}
	cmdReader, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}
	scanner := bufio.NewScanner(cmdReader)
	go func() {
		for scanner.Scan() {
			fmt.Println(scanner.Text())
		}
	}()
	if err := cmd.Start(); err != nil {
		log.Fatal(err)
	}
	if err := cmd.Wait(); err != nil {
		log.Fatal(err)
	}
}

func dbConnect(connect string) *sql.DB {
	psqlParam := fmt.Sprintf("%v?sslmode=disable&fallback_application_name=deployer", connect)
	db, err := sql.Open("postgres", psqlParam)
	checkFatal(err)
	return db
}

func checkErr(err error) {
	if err != nil {
		log.Print(err)
	}
}

func checkFatal(err error) {
	if err != nil {
		log.Fatal(err)
	}
}
