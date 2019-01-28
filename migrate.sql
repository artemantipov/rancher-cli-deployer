create database db_acl;

create table if not exists users
(
  id   serial       not null
    constraint users_pk
    primary key,
  name varchar(255) not null
);
alter table users
  owner to postgres;
create unique index if not exists users_name_uindex
  on users (name);

create table if not exists stacks
(
  id    serial       not null
    constraint stacks_pk
    primary key,
  stack varchar(255) not null
);
alter table stacks
  owner to postgres;
create unique index if not exists stacks_stack_uindex
  on stacks (stack);

create table if not exists groups
(
  id      serial       not null
    constraint groups_pk
    primary key,
  "group" varchar(255) not null
);
alter table groups
  owner to postgres;
create unique index if not exists groups_group_uindex
  on groups ("group");

create table if not exists users_in_group
(
  user_id  integer
    constraint users_in_group_users_id_fk
    references users,
  group_id integer
    constraint users_in_group_groups_id_fk
    references groups
);
alter table users_in_group
  owner to postgres;

create table if not exists stack_in_group
(
  group_id integer
    constraint stack_in_group_groups_id_fk
    references groups,
  stack_id integer
    constraint stack_in_group_stacks_id_fk
    references stacks
);
alter table stack_in_group
  owner to postgres;
  
create view acl_view as
  SELECT u.name, g."group", s.stack
  FROM ((((users_in_group uig
      JOIN stack_in_group sig ON ((uig.group_id = sig.group_id)))
      JOIN users u ON ((uig.user_id = u.id)))
      JOIN stacks s ON ((sig.stack_id = s.id)))
      JOIN groups g ON ((sig.group_id = g.id)));
alter table acl_view
  owner to postgres;