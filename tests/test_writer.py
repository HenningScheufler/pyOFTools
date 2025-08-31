from pyOFTools.datasets import AggregatedDataSet, AggregatedData, InternalDataSet
from pyOFTools.workflow import Workflow
from pyOFTools.writer import CSVWriter
import os
import pytest

@pytest.fixture
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)

def test_aggregated_dataset(change_test_dir):
    dataset = AggregatedDataSet(
        name="test_aggregated",
        values=[
            AggregatedData(name="data1", value=1.0),
            AggregatedData(name="data2", value=2.0),
        ],
    )
    writer = CSVWriter(name="test_output")
    writer.create_file()
    
    # Use the dataset to verify it was created correctly

    assert dataset.name == "test_aggregated"
    assert len(dataset.values) == 2
    assert os.path.isfile("test_output.csv")

    assert writer.write_data(dataset)
