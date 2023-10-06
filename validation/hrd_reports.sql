with all_reports as (
  select  order_id,
                  reports.uploaded,
                  sdo.source_data -> 0 -> 'data' -> '$metadata' -> 'bioinformaticsHrdOutput0Id' ->> 0        as analysis_id,
                  sdo.source_data -> 0 -> 'data' -> 'reportModuleNormal' -> '$moduleData' -> 'hrd_result' ->> 0 as hrd_result,
                  rd.update_reason
  from reports
         inner join report_drafts rd on reports.id = rd.report_id
         inner join source_data_objects sdo on rd.source_data_id = sdo.id
  where reports.report_type_name = 'hrd'
    and reports.test = false
),
     unique_reports as (
       select distinct order_id
                     , uploaded
                     , analysis_id
                     , hrd_result
                     , string_agg(update_reason, ', ') as report_notes
       from all_reports
       group by order_id
              , uploaded
              , analysis_id
              , hrd_result
     )
select *
     , case when report_notes ilike '%aneup%' then 1 else 0 end as anueploidy
from unique_reports
