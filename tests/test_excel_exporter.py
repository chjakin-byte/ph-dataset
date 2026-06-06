import os
import pytest
from app.exporters.excel import ExcelExporter
from app.models.evidence import RawEvidence, MappedEvidence
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
            relevance_score=0.9
        )
    ]
    
    mapped = [
        MappedEvidence(
            **raw[0].model_dump(),
            module="Market",
            conclusion="Test conclusion"
        )
    ]
    
    exporter.export(raw, mapped)
    
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
