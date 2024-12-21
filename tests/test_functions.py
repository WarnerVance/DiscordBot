import pytest
import pandas as pd
import os
import time
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Add project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions as fn

# Fixtures
@pytest.fixture
def setup_test_files():
    """Create test files before each test and clean up after"""
    # Create test directories
    os.makedirs('backups', exist_ok=True)
    
    # Create test pledges.csv
    with open('pledges.csv', 'w') as f:
        f.write("TestPledge1\nTestPledge2\nTestPledge3\n")
    
    # Create test Points.csv
    test_points = pd.DataFrame({
        'Time': [time.time(), time.time() - 86400],  # Now and 24h ago
        'Name': ['TestPledge1', 'TestPledge2'],
        'Point_Change': [10, -5],
        'Comments': ['Test comment 1', 'Test comment 2']
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
    for file in ['pledges.csv', 'Points.csv', 'PendingPoints.csv', 
                 'pledge_points_graph.png', 'points_over_time.png']:
        if os.path.exists(file):
            os.remove(file)
    
    # Clean up backup directory
    if os.path.exists('backups'):
        for file in os.listdir('backups'):
            os.remove(os.path.join('backups', file))
        os.rmdir('backups')

# Test File Operations
def test_file_creation(setup_test_files):
    """Test automatic file creation"""
    # Remove all files
    for file in ['pledges.csv', 'Points.csv', 'PendingPoints.csv']:
        if os.path.exists(file):
            os.remove(file)
    
    # Test get_points_csv creates file
    df = fn.get_points_csv()
    assert os.path.exists('Points.csv')
    assert list(df.columns) == ["Time", "Name", "Point_Change", "Comments"]
    
    # Test get_pending_points_csv creates file
    df = fn.get_pending_points_csv()
    assert os.path.exists('PendingPoints.csv')
    assert list(df.columns) == ["Time", "Name", "Point_Change", "Comments", "Requester"]

# Test Pledge Management
def test_pledge_operations(setup_test_files):
    """Test pledge management functions"""
    # Test adding pledges
    assert fn.add_pledge("NewPledge") == 0
    assert fn.add_pledge("TestPledge1") == 1  # Duplicate
    assert fn.add_pledge("") == 1  # Empty name
    assert fn.add_pledge("Very" * 20) == 1  # Too long
    
    # Test checking pledges
    assert fn.check_pledge("TestPledge1") == True
    assert fn.check_pledge("NonexistentPledge") == False
    
    # Test getting pledges
    pledges = fn.get_pledges()
    assert "TestPledge1" in pledges
    assert "NewPledge" in pledges
    assert len(pledges) >= 4
    
    # Test deleting pledges
    assert fn.delete_pledge("TestPledge1") == 0
    assert fn.delete_pledge("NonexistentPledge") == 1
    assert not fn.check_pledge("TestPledge1")

# Test Points System
def test_points_system(setup_test_files):
    """Test points management system"""
    # Test point updates
    assert fn.update_points("TestPledge1", 5, "Test update") == 0
    assert fn.update_points("NonexistentPledge", 5, "Test") == 1
    assert fn.update_points("TestPledge1", "invalid", "Test") == 1
    assert fn.update_points("TestPledge1", 5, "") == 1
    
    # Test point retrieval
    points = fn.get_pledge_points("TestPledge1")
    assert isinstance(points, (int, float, np.integer, np.floating))
    assert points == 15  # 10 from setup + 5 from update
    assert fn.get_pledge_points("NonexistentPledge") is None

# Test Pending Points System
def test_pending_points_system(setup_test_files):
    """Test pending points functionality"""
    # Test adding pending points
    assert fn.add_pending_points("TestPledge1", 5, "New pending", "TestBrother") == 0
    assert fn.add_pending_points("NonexistentPledge", 5, "Test", "TestBrother") == 1
    
    # Test approving points
    success, message, data = fn.approve_pending_points(0)
    assert success == True
    assert data['Point_Change'] == 5
    
    # Test rejecting points
    assert fn.add_pending_points("TestPledge2", 5, "Test reject", "TestBrother") == 0
    success, message, data = fn.reject_pending_points(0)
    assert success == True
    assert data['Point_Change'] == 5

# Test Visualization Functions
def test_visualization_functions(setup_test_files):
    """Test graph generation functions"""
    # Test points graph
    graph_file = fn.get_points_graph()
    assert os.path.exists(graph_file)
    assert graph_file.endswith('.png')
    
    # Test points over time
    timeline_file = fn.get_points_over_time()
    assert os.path.exists(timeline_file)
    assert timeline_file.endswith('.png')
    
    # Verify images are valid
    plt.imread(graph_file)
    plt.imread(timeline_file)

# Test Role Checking
@pytest.mark.asyncio
async def test_role_checking():
    """Test role verification functions"""
    # Test Brother role check
    mock_interaction = MagicMock()
    brother_role = MagicMock()
    brother_role.name = "Brother"  # Set the role name explicitly
    
    # Set up the mock interaction with proper role structure
    mock_interaction.guild = MagicMock()
    mock_interaction.guild.roles = [brother_role]
    mock_interaction.user = MagicMock()
    mock_interaction.user.roles = [brother_role]
    mock_interaction.response = MagicMock()
    mock_interaction.response.send_message = AsyncMock()
    
    # Test Brother role present
    assert await fn.check_brother_role(mock_interaction) == True
    
    # Test Brother role absent
    mock_interaction.user.roles = []
    assert await fn.check_brother_role(mock_interaction) == False
    
    # Test VP Internal role check
    vp_role = MagicMock()
    vp_role.name = "VP Internal"  # Set the role name explicitly
    mock_interaction.guild.roles = [vp_role]
    mock_interaction.user.roles = [vp_role]
    
    # Test VP Internal role present
    assert await fn.check_vp_internal_role(mock_interaction) == True
    
    # Test VP Internal role absent
    mock_interaction.user.roles = []
    assert await fn.check_vp_internal_role(mock_interaction) == False

# Test Error Handling
def test_error_handling(setup_test_files):
    """Test error handling in various scenarios"""
    # Test file operations with invalid permissions
    with patch('builtins.open', side_effect=PermissionError):
        df = fn.get_points_csv()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    
    # Test with corrupted files
    with open('Points.csv', 'w') as f:
        f.write("corrupted,data\n")
    df = fn.get_points_csv()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Time", "Name", "Point_Change", "Comments"]

# Test Data Validation
def test_data_validation(setup_test_files):
    """Test input validation functions"""
    # Test point change validation
    assert fn.update_points("TestPledge1", 35, "Valid") == 0
    assert fn.update_points("TestPledge1", -35, "Valid") == 0
    assert fn.update_points("TestPledge1", 36, "Invalid") == 1
    assert fn.update_points("TestPledge1", -36, "Invalid") == 1
    
    # Test comment validation
    long_comment = "x" * 501
    result = fn.update_points("TestPledge1", 5, long_comment)
    assert result == 0
    df = fn.get_points_csv()
    assert len(df.iloc[-1]['Comments']) <= 500
  