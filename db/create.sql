drop type backend cascade;
drop type signal_type cascade;
drop type frontend cascade;
drop type mech cascade;
drop type scan cascade;
drop table ac_level0 cascade;
drop table ac_level1a cascade;
drop table fba_level0;
drop table attitude_level0 cascade;
drop table attitude_level1 cascade;

create type backend as enum ('AC1','AC2');
create type signal_type as enum ('REF','SIG');
create type frontend as enum ('549','495','572','555','SPL','119');
create type mech as enum ('REF','SK1','CAL','SK2');
create type scan as (start bigint, stw bigint);

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

create table fba_level0(
   stw bigint,
   mech_type mech,
   constraint pk_fba_level0 primary key (stw)
);

create table attitude_level0(
   stw bigint,
   year int,
   mon int,
   day int,
   hour int,
   min int,
   secs real,
   orbit real,
   qt real[4],
   qa real[4],
   qe real[3],
   gps real[6],
   acs real,
   constraint pk_attitudelevel0_data primary key (stw)
);

create table attitude_level1(
   stw bigint,
   backend backend,     
   latitude real,
   longitude real,
   altitude real,
   constraint pk_attitudelevel1_data primary key (stw,backend)
);

CREATE OR REPLACE FUNCTION public.getscans()
 RETURNS SETOF scan
 LANGUAGE plpgsql
AS $function$
declare
   spectrum_curs cursor for select * from fba_level0 order by stw;
   res scan%rowtype;
   prev_mech fba_level0.mech_type%type;
   scanstart fba_level0.stw%type;
begin
   prev_mech:='SK1';
   scanstart:=-1;
   
   for r in spectrum_curs loop
      if r.mech_type='CAL' and prev_mech<>'CAL' then
         scanstart:=r.stw;
      end if;
      res.start:=scanstart;
      res.stw:=r.stw;
      prev_mech:=r.mech_type; 
      return next res;
   end loop;
   return;
end;
$function$
