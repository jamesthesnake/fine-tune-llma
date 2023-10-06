from hrd_models.rna_predictor.rna_predictor import RNAPredictor
import s3fs
import sqlalchemy as sa
import os
import pandas as pd
import pymysql
from tdsu.settings import STG_BIOINF_URL


def get_intraassay_metadata():
    intraassay_isolates = [
        "20-A42444_RSQ1",
        "20-A42445_RSQ1",
        "20-A42446_RSQ1",
        "20-A42447_RSQ1",
        "20-A42448_RSQ1",
        "20-A42449_RSQ1",
        "20-A42450_RSQ1",
        "20-A42451_RSQ1",
        "20-A42452_RSQ1",
        "20-A42453_RSQ1",
        "20-A42454_RSQ1",
        "20-A42455_RSQ1",
        "20-A42456_RSQ1",
        "20-A42457_RSQ1",
        "20-A42458_RSQ1",
        "20-A42459_RSQ1",
        "20-A42460_RSQ1",
        "20-A42461_RSQ1",
        "20-A42462_RSQ1",
        "20-A42463_RSQ1",
    ]

    return get_metadata(intraassay_isolates)


def get_interassay_metadata():
    interassay_isolates = [
        "20-POS14828_RSQ5",
        "20-POS14828_RSQ4",
        "20-A42481_RSQ4",
        "20-A42481_RSQ5",
        "20-A42475_RSQ3",
        "20-A42474_RSQ4",
        "20-A42475_RSQ4",
        "20-A42475_RSQ5",
        "20-A42488_RSQ5",
        "20-A42487_RSQ4",
        "20-A42474_RSQ5",
        "20-POS14828_RSQ3",
        "20-A42487_RSQ5",
        "20-A42482_RSQ5",
        "20-A42481_RSQ3",
        "20-A42488_RSQ3",
        "20-A42474_RSQ3",
        "20-A42487_RSQ3",
        "20-A42488_RSQ4",
        "20-A42482_RSQ4",
        "20-A42482_RSQ3",
        "20-POS14828_RSQ7b",
        "20-A42481_RSQ7b",
        "20-A42474_RSQ7b",
        "20-A42482_RSQ6",
        "20-A42475_RSQ7b",
        "20-A42488_RSQ6",
        "20-POS14828_RSQ6",
        "20-A42474_RSQ6",
        "20-A42481_RSQ6",
        "20-A42475_RSQ6",
        "20-A42488_RSQ7b",
        "20-A42487_RSQ7b",
        "20-A42482_RSQ7b",
        "20-A42474_RSQ2",
        "20-A42487_RSQ1",
        "20-POS14828_RSQ2",
        "20-A42475_RSQ2",
        "20-A42488_RSQ2",
        "20-POS14828_RSQ1",
        "20-A42474_RSQ1",
        "20-A42482_RSQ1",
        "20-A42488_RSQ1",
        "20-A42481_RSQ1",
        "20-A42475_RSQ1",
        "20-A42482_RSQ2",
        "20-A42481_RSQ2",
        "20-A42487_RSQ2",
    ]
    return get_metadata(interassay_isolates)


def get_metadata(isolate_ids: list):

    con = sa.create_engine(STG_BIOINF_URL)
    metadata = pd.read_sql(
        f"""
        select distinct ao.analysis_id
                      , ai.isolate_id sample_id
                      , ao.url abundance_url
        from analysis_output ao
        left join analysis_isolate ai using (analysis_id)
        left join analysis a on a.id =  ao.analysis_id
        where isolate_id in {tuple(isolate_ids)}
        and type = 'rna_expression_abundance'
        and intent = '3.0.2-rsv2val'
            """,
        con,
    )
    return metadata


def normalize(metadata: pd.DataFrame):

    # Read abundance files and normalize
    normalized = pd.DataFrame()
    for i, row in metadata.iterrows():
        rna = RNAPredictor()
        abundance = pd.read_csv(row.abundance_url, delimiter="\t")
        normalized = normalized.append(rna.normalize_abundance(abundance))
        print(i)
    normalized = normalized.set_index(metadata.sample_id)

    return normalized


def main():
    # Output filenames
    intraassay_filename = "/data/analysis/hrd/validation/inter_intra_assay/intraassay_rna_normalized.parquet"
    interassay_filename = "/data/analysis/hrd/validation/inter_intra_assay/intrasequencer_rna_normalized.parquet"

    # Get metadata (abundance URLs)
    intraassay = get_intraassay_metadata()
    interassay = get_interassay_metadata()

    # Normalize abundance files
    intraassay = normalize(intraassay)
    interassay = normalize(interassay)

    # Save to EFS
    intraassay.to_parquet(intraassay_filename)
    interassay.to_parquet(interassay_filename)


if __name__ == "__main__":
    main()
