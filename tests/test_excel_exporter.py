import os
import pytest
from app.exporters.excel import ExcelExporter
from app.models.evidence import RawEvidence, MappedEvidence, DataQualityMetric
from datetime import datetime

def test_excel_export():
    output_path = "output/test_report.xlsx"
    if os.path.exists(output_path):
        os.remove(output_path)
        
    exporter = ExcelExporter(output_path)
    
    raw = [
        RawEvidence(
            source_platform="TestPlatform",
            source_location="http://test.com",
            timestamp=datetime.now(),
            extracted_text="Test raw data",
            evidence_score=90.0,
            frequency=1
        )
    ]
    
    mapped = [
        MappedEvidence(
            **raw[0].model_dump(),
            module="Market",
            conclusion="Test conclusion"
        )
    ]
    
    quality = [
        DataQualityMetric(
            metric_name="Test Metric",
            value=100.0,
            notes="Test notes"
        )
    ]
    
    stats = {
        "Total Projects": 1
    }
    
    exporter.export(raw, mapped, quality, stats)
    
    assert os.path.exists(output_path)
    
    import pandas as pd
    xl = pd.ExcelFile(output_path)
    
    assert "Market" in xl.sheet_names
    market_df = xl.parse("Market")
    
    assert not market_df.empty
    assert "extracted_text" in market_df.columns
    assert "conclusion" in market_df.columns
    assert market_df.iloc[0]["extracted_text"] == "Test raw data"
    assert market_df.iloc[0]["conclusion"] == "Test conclusion"
