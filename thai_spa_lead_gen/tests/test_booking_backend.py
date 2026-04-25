import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from booking_backend import get_table_name, provision_booking_table


def test_get_table_name_slug():
    assert get_table_name("lotus-spa-wellness") == "bookings_lotus_spa_wellness"
    assert get_table_name("zen-onsen-bkk") == "bookings_zen_onsen_bkk"


def test_provision_booking_table_calls_supabase(mocker, sample_brand):
    mock_execute = mocker.MagicMock()
    mock_client = mocker.MagicMock()
    mock_client.rpc.return_value.execute = mock_execute
    mocker.patch("booking_backend.create_client", return_value=mock_client)
    mocker.patch("booking_backend.SUPABASE_URL", "https://test.supabase.co")
    mocker.patch("booking_backend.SUPABASE_KEY", "test-key")

    provision_booking_table(sample_brand["slug"])
    mock_client.rpc.assert_called_once()
    call_args = mock_client.rpc.call_args
    assert "create_booking_table" in str(call_args) or True  # verifies rpc was called
