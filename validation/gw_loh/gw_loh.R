library(tidyverse)

root_dir <- '/data/analysis/hrd/validation/gwloh_ex'
order_level <- glue('{root_dir}/20210310-065803-10k-order_level.csv') %>% read.csv
gene_level <- glue('{root_dir}/20210310-065803-10k-gene_level.csv') %>% read.csv

# Discrepancies between automated pipeline and pathology
matched <- gene_level %>% 
  tibble %>% 
  inner_join( # Matched analyses only
    order_level %>% 
      filter(match_type == 'match',
             assay %in% c('xT.v2', 'xT.v4')) %>% 
      select(analysis_id)
  ) %>% 
  # Filter to patients with no single hits in interested genes
  filter(interested_gene == 1,
         single_hit == 0) %>% 
  mutate(deep_loss_summary = case_when(
    deep_loss_reported == 0 & deep_loss_reportable == 0 ~ 'Both negative',
    deep_loss_reported == 1 & deep_loss_reportable == 1 ~ 'Both positive', 
    deep_loss_reported == 1 & deep_loss_reportable == 0 ~ 'Pathology only',
    deep_loss_reported == 0 & deep_loss_reportable == 1 ~ 'Bioinformatics only',
  )) %>% 
  mutate(loh_summary = case_when(
    loh_reported == 0 & loh_reportable == 0 ~ 'Both negative',
    loh_reported == 1 & loh_reportable == 1 ~ 'Both positive', 
    loh_reported == 1 & loh_reportable == 0 ~ 'Pathology only',
    loh_reported == 0 & loh_reportable == 1 ~ 'Bioinformatics only',
  ))

matched %>% filter(deep_loss_summary == 'Bioinformatics only') %>% glimpse
