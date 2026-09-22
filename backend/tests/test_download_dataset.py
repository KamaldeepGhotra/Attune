import httpx
import respx

from scripts.download_dataset import DATASET_URL, download_dataset


@respx.mock
def test_download_dataset_writes_file_when_missing(tmp_path):
    dest = tmp_path / "dataset.csv"
    respx.get(DATASET_URL).mock(return_value=httpx.Response(200, content=b"track_id,tempo\nabc,120\n"))

    download_dataset(str(dest))

    assert dest.read_bytes() == b"track_id,tempo\nabc,120\n"


@respx.mock
def test_download_dataset_skips_when_already_present(tmp_path):
    dest = tmp_path / "dataset.csv"
    dest.write_bytes(b"already here")
    route = respx.get(DATASET_URL).mock(return_value=httpx.Response(200, content=b"new content"))

    download_dataset(str(dest))

    assert dest.read_bytes() == b"already here"
    assert route.call_count == 0
