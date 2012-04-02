drop type backend cascade;
drop type signal_type cascade;
drop type frontend cascade;
drop table ac_level0 cascade;
drop table ac_level1a cascade;

create type backend as enum ('AC1','AC2');
create type signal_type as enum ('REF','SIG');
create type frontend as enum ('549','495','572','555','SPL','119');


create table ac_level0(
   stw bigint,
   backend backend,
   frontend frontend,
   sig_type signal_type,
   ssb_att int[4],
   ssb_fq int[4],
   prescaler int,
   inttime real,
   mode int,
   acd_mon bytea,
   cc bytea,
   constraint pk_ac_data primary key (backend,stw)
);

create table ac_level1a(
   stw bigint,
   backend backend,
   spectra bytea,
   constraint pk_aclevel1a_data primary key (backend,stw)
);