import csv
import pandas as pd
import warnings

warnings.filterwarnings("ignore")
# from hrd_models.dna_predictor.variant_parser import ReportedVariantParser
# from hrd_models.dna_predictor.copy_number_calculations import get_gene_loss_percent

from hrd_models.common.file_reader import decode_tsv_file
from hrd_models.dna_predictor.dna_predictor import DNAPredictor

#! Cona Files
# variants_file = 'test-data/be453ef6-3040-4242-a32e-f76068624b32.dna_variant.csv'
# stats_file = 'test-data/be453ef6-3040-4242-a32e-f76068624b32.annotated_cnv_v2.cnv_stats.csv'
# cnv_file = 'test-data/be453ef6-3040-4242-a32e-f76068624b32.annotated_cnv_v2.csv'

#! Re-orchestrated Files
reported_variants_file = "test-data/4d44d060-fd81-4e5e-b4c4-f9f6737ea1f2-edited.tsv"
raw_variants_file = "test-data/10196c56-184f-4040-9fef-4e7b44a441f4.dna_variant.csv"
cnv_file = "test-data/4d44d060-fd81-4e5e-b4c4-f9f6737ea1f2.annotated_cnv_v2.csv"

cancer_cohort = "Peritoneal Cancer"
stats_data = []

#! Patching in file reading logic
reported_variants_df, meta = decode_tsv_file(reported_variants_file)
raw_variants_df = pd.read_csv(raw_variants_file)
copy_number_data = pd.read_csv(cnv_file)
dnp = DNAPredictor(
    cancer_cohort, copy_number_data, reported_variants_df, raw_variants_df
)
prediction = dnp.predict()
print(prediction["order_level"].T)
print(prediction["gene_level"].T)
prediction["gene_level"].to_csv("test-gene-out.csv", sep="\t")
prediction["order_level"].to_csv("test-order-out.csv", sep="\t")
