import pytest
import pandas as pd
import os
import time
from unittest.mock import MagicMock, patch
import numpy as np

# Add project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions as fn

# Fixture to create temporary test files
@pytest.fixture
def setup_test_files():
    # Create test pledges.csv
    with open('pledges.csv', 'w') as f:
        f.write("TestPledge1\nTestPledge2\n")
    
    # Create test Points.csv with a known point value
    test_points = pd.DataFrame({
        'Time': [time.time()],
        'Name': ['TestPledge1'],
        'Point_Change': [10],
        'Comments': ['Test comment']
    })
    test_points.to_csv('Points.csv', index=False)
    
    # Create test PendingPoints.csv
    test_pending = pd.DataFrame({
        'Time': [time.time()],
        'Name': ['TestPledge1'],
        'Point_Change': [5],
        'Comments': ['Pending test'],
        'Requester': ['TestBrother']
    })
    test_pending.to_csv('PendingPoints.csv', index=False)
    
    yield
    
    # Cleanup
    for file in ['pledges.csv', 'Points.csv', 'PendingPoints.csv']:
        if os.path.exists(file):
            os.remove(file)

# Test pledge management functions
def test_check_pledge(setup_test_files):
    assert fn.check_pledge("TestPledge1") == True
    assert fn.check_pledge("NonexistentPledge") == False

def test_add_pledge(setup_test_files):
    assert fn.add_pledge("NewPledge") == 0  # Success
    assert fn.add_pledge("TestPledge1") == 1  # Already exists
    assert fn.check_pledge("NewPledge") == True

def test_get_pledges(setup_test_files):
    pledges = fn.get_pledges()
    assert "TestPledge1" in pledges
    assert "TestPledge2" in pledges
    assert len(pledges) == 2

def test_delete_pledge(setup_test_files):
    assert fn.delete_pledge("TestPledge1") == 0  # Success
    assert fn.delete_pledge("NonexistentPledge") == 1  # Failure
    assert fn.check_pledge("TestPledge1") == False

# Test points management functions
def test_get_points_csv(setup_test_files):
    df = fn.get_points_csv()
    assert isinstance(df, pd.DataFrame)
    assert all(col in df.columns for col in ['Time', 'Name', 'Point_Change', 'Comments'])

def test_update_points(setup_test_files):
    assert fn.update_points("TestPledge1", 5, "Test update") == 0  # Success
    assert fn.update_points("NonexistentPledge", 5, "Test") == 1  # Failure
    assert fn.update_points("TestPledge1", "invalid", "Test") == 1  # Invalid points

def test_get_pledge_points(setup_test_files):
    # First verify the test data exists and print it for debugging
    df = pd.read_csv('Points.csv')
    print(f"Test data in Points.csv:\n{df}")  # Debug print
    assert len(df) > 0
    
    points = fn.get_pledge_points("TestPledge1")
    print(f"Points for TestPledge1: {points}")  # Debug print
    assert isinstance(points, (int, float, np.integer, np.floating))
    assert points == 10
    assert fn.get_pledge_points("NonexistentPledge") is None

# Test pending points system
def test_get_pending_points_csv(setup_test_files):
    df = fn.get_pending_points_csv()
    assert isinstance(df, pd.DataFrame)
    assert all(col in df.columns for col in ['Time', 'Name', 'Point_Change', 'Comments', 'Requester'])

def test_add_pending_points(setup_test_files):
    assert fn.add_pending_points("TestPledge1", 5, "Test pending", "TestBrother") == 0  # Success
    assert fn.add_pending_points("NonexistentPledge", 5, "Test", "TestBrother") == 1  # Failure

def test_approve_pending_points(setup_test_files):
    success, message, data = fn.approve_pending_points(0)  # First pending entry
    assert success == True
    assert "approved" in message.lower()
    assert data['Point_Change'] == 5

def test_reject_pending_points(setup_test_files):
    success, message, data = fn.reject_pending_points(0)  # First pending entry
    assert success == True
    assert "rejected" in message.lower()
    assert data['Point_Change'] == 5

# Test role checking (mocked Discord interaction)
@pytest.mark.asyncio
async def test_check_brother_role():
    mock_interaction = MagicMock()
    # Create a proper role mock with name property
    brother_role = MagicMock()
    brother_role.name = "Brother"
    
    mock_interaction.guild.roles = [brother_role]
    mock_interaction.user.roles = [brother_role]
    
    async def async_return(*args, **kwargs):
        return None
    mock_interaction.response.send_message = MagicMock(side_effect=async_return)
    
    # Debug prints
    print(f"Guild roles: {[r.name for r in mock_interaction.guild.roles]}")
    print(f"User roles: {[r.name for r in mock_interaction.user.roles]}")
    
    result = await fn.check_brother_role(mock_interaction)
    assert result == True
    
    # Test without Brother role
    mock_interaction.user.roles = []
    result = await fn.check_brother_role(mock_interaction)
    assert result == False

@pytest.mark.asyncio
async def test_check_vp_internal_role():
    mock_interaction = MagicMock()
    # Create a proper role mock with name property
    vp_role = MagicMock()
    vp_role.name = "VP Internal"
    
    mock_interaction.guild.roles = [vp_role]
    mock_interaction.user.roles = [vp_role]
    
    async def async_return(*args, **kwargs):
        return None
    mock_interaction.response.send_message = MagicMock(side_effect=async_return)
    
    # Debug prints
    print(f"Guild roles: {[r.name for r in mock_interaction.guild.roles]}")
    print(f"User roles: {[r.name for r in mock_interaction.user.roles]}")
    
    result = await fn.check_vp_internal_role(mock_interaction)
    assert result == True
    
    # Test without VP Internal role
    mock_interaction.user.roles = []
    result = await fn.check_vp_internal_role(mock_interaction)
    assert result == False

# Test error handling
def test_error_handling(setup_test_files):
    # Test with invalid inputs
    assert fn.update_points("", 5, "Test") == 1  # Empty name
    assert fn.update_points("TestPledge1", None, "Test") == 1  # Invalid points
    assert fn.update_points("TestPledge1", 5, "") == 1  # Empty comment

# Test file operations
def test_file_operations(setup_test_files):
    # Test file creation
    os.remove('Points.csv')
    df = fn.get_points_csv()
    assert os.path.exists('Points.csv')
    assert isinstance(df, pd.DataFrame)
    
    os.remove('PendingPoints.csv')
    df = fn.get_pending_points_csv()
    assert os.path.exists('PendingPoints.csv')
    assert isinstance(df, pd.DataFrame) 