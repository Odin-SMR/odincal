drop type backend cascade;
drop type signal_type cascade;
drop type frontend cascade;
drop type mech cascade;
drop type scan cascade;
drop type shk_type cascade;
drop type sourcemode cascade;
drop type spectype cascade;

drop table ac_level0 cascade;
drop table ac_level1a cascade;
drop table ac_level1b cascade;
drop table ac_level1bn cascade;
drop table ac_cal_level1b cascade;
drop table fba_level0;
drop table attitude_level0 cascade;
drop table attitude_level1 cascade;
drop table shk_level0 cascade;
drop table shk_level1 cascade;
drop table process cascade;

create type backend as enum ('AC1','AC2');
create type signal_type as enum ('REF','SIG');
create type frontend as enum ('549','495','572','555','SPL','119');
create type mech as enum ('REF','SK1','CAL','SK2');
create type scan as (start bigint, stw bigint);
create type shk_type as enum ('LO495','LO549','LO555','LO572','SSB495','SSB549',
'SSB555','SSB572','mixC495','mixC549','mixC555','mixC572','imageloadB',
'hotloadA','hotloadB');
create type shk_typenew as enum ('LO495','LO549','LO555','LO572','SSB495','SSB549','SSB555','SSB572','mixC495','mixC549','mixC555','mixC572','imageloadA','imageloadB','hotloadA','hotloadB','mixerA','mixerB','lnaA','lnaB','119mixerA','119mixerB','warmifA','warmifB');


create type sourcemode as enum ('STRAT','ODD_H','ODD_N','WATER','SUMMER',
'DYNAM');
create type sourcemoden as enum ('STRAT','ODD_H','ODD_N','WATER','SUMMER',
'DYNAM','N/A');

create type spectype as enum ('SIG','REF','CAL','CMB','DRK','SK1','SK2','SPE',
'SSB','AVE');

create table process(
   orbit int,
   backend backend,
   stws bytea,
   stws_shape varchar,
   processed int,
   constraint pk_process_data primary key (orbit,backend)
);

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

create table ac_level1bn(
   stw bigint,
   backend backend,
   version int,
   intmode int,
   soda int,
   spectra bytea,
   channels int,
   skyfreq double precision,
   lofreq double precision,
   restfreq double precision,
   maxsuppression double precision,
   tsys real,
   sourcemode sourcemoden,
   freqmode int,
   efftime real,
   sbpath real,
   calstw bigint,
   constraint pk_aclevel1bn_data primary key (backend,stw,version,intmode,soda)
);

create table ac_cal_level1b(
   stw bigint,
   backend backend,
   version int, 
   spectype spectype,
   intmode int,
   soda int,
   spectra bytea,
   channels int,
   skyfreq double precision,
   lofreq double precision,
   restfreq double precision,
   maxsuppression double precision,
   sourcemode sourcemode,
   freqmode int,
   sbpath real,
   tspill real,
   constraint pk_accallevel1b_data primary key (backend,stw,version,spectype,intmode,soda)
);

create table fba_level0(
   stw bigint,
   mech_type mech,
   constraint pk_fba_level0 primary key (stw)
);

create table attitude_level0(
   stw bigint,
   soda int,
   year int,
   mon int,
   day int,
   hour int,
   min int,
   secs double precision,
   orbit double precision,
   qt double precision[4],
   qa double precision[4],
   qe double precision[3],
   gps double precision[6],
   acs double precision,
   constraint pk_attitudelevel0_data primary key (stw,soda)
);

create table attitude_level1(
   stw bigint,
   backend backend,
   soda int, 
   mjd double precision,
   lst real, 
   orbit double precision,   
   latitude real,
   longitude real,
   altitude real,
   skybeamhit int,
   ra2000 real,
   dec2000 real,
   vsource real,
   qtarget double precision[4],
   qachieved double precision[4],
   qerror double precision[3],
   gpspos double precision[3],
   gpsvel double precision[3],
   sunpos double precision[3],
   moonpos double precision[3],
   sunzd real,
   vgeo real,
   vlsr real,   
   alevel int,
   constraint pk_attitudelevel1_data primary key (stw,backend,soda)
);

create table shk_level0(
   stw bigint,
   shk_type shk_type,
   shk_value real,
   constraint pk_shklevel0_data primary key (stw,shk_type)
);
create table shk_level0n(
   stw bigint,
   shk_type shk_typenew,
   shk_value real,
   constraint pk_shklevel0n_data primary key (stw,shk_type)
);

create table shk_level1(
   stw bigint,
   backend backend,
   frontendsplit frontend,
   LO real,
   SSB real,
   mixC real,
   imageloadB real,
   hotloadA real,
   hotloadB real,
   constraint pk_shklevel1_data primary key (stw,backend,frontendsplit)
);

create table shk_level1n(
   stw bigint,
   backend backend,
   frontendsplit frontend,
   LO real,
   SSB real,
   mixC real,
   imageloadA real,
   imageloadB real,
   hotloadA real,
   hotloadB real,
   mixerA real, 
   mixerB real, 
   lnaA real,
   lnaB real,
   mixer119A real,
   mixer119B real,
   warmifA real,
   warmifB real,
   constraint pk_shklevel1n_data primary key (stw,backend,frontendsplit)
);


CREATE OR REPLACE FUNCTION public.getscansac2()
 RETURNS SETOF scan
 LANGUAGE plpgsql
AS $function$
declare
   spectrum_curs cursor for select fba_level0.stw,mech_type from fba_level0 
   natural join ac_level0 
   order by stw;
   res scan%rowtype;
   prev_mech fba_level0.mech_type%type;
   scanstart fba_level0.stw%type;
begin
   prev_mech:='SK1';
   scanstart:=-1;
   
   for r in spectrum_curs loop
      if r.mech_type='CAL' and prev_mech<>'CAL'  then
         scanstart:=r.stw;
      end if;
      res.start:=scanstart;
      res.stw:=r.stw;
      prev_mech:=r.mech_type; 
      return next res;
   end loop;
   return;
end;
$function$;

CREATE OR REPLACE FUNCTION public.getscansac1()
 RETURNS SETOF scan
 LANGUAGE plpgsql
AS $function$
declare
   spectrum_curs cursor for select fba_level0.stw,mech_type from fba_level0 
   join ac_level0 on (fba_level0.stw+1=ac_level0.stw)
   order by stw;
   res scan%rowtype;
   prev_mech fba_level0.mech_type%type;
   scanstart fba_level0.stw%type;
begin
   prev_mech:='SK1';
   scanstart:=-2;
   
   for r in spectrum_curs loop
      if r.mech_type='CAL' and prev_mech<>'CAL' then
         scanstart:=r.stw;
      end if;
      res.start:=scanstart+1;
      res.stw:=r.stw+1;
      prev_mech:=r.mech_type; 
      return next res;
   end loop;
   return;
end;
$function$;
