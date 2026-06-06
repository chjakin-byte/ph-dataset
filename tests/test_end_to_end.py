import os
import pytest
from app.runner import PipelineRunner
import pandas as pd

def test_pipeline_end_to_end():
    # Ensure a fresh state
    if os.path.exists("output/kickstarter_research_report.xlsx"):
        os.remove("output/kickstarter_research_report.xlsx")
        
    # Run the pipeline
    runner = PipelineRunner("config.yaml")
    runner.run()
    
    # Check that output Excel exists
    assert os.path.exists("output/kickstarter_research_report.xlsx")
    
    # Verify sheets in Excel (now 15 sheets)
    xl = pd.ExcelFile("output/kickstarter_research_report.xlsx")
    required_sheets = [
        "Summary", "Raw Evidence", "Market", "User", "Pain Points", 
        "Competitors", "Evidence", "Launch Strategy", "Risk", 
        "Final Recommendation", "Signal Detection", "Opportunity Score", 
        "Data Quality", "Logs", "Errors"
    ]
    for sheet in required_sheets:
        assert sheet in xl.sheet_names

    # Check non-empty sheets (Summary at least should have data)
    summary_df = xl.parse("Summary")
    assert not summary_df.empty
