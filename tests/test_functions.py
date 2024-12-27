import os
# Add project root to Python path
import sys
import time
from unittest.mock import MagicMock, patch, AsyncMock

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import CheckRoles
import Interviews
import PointSystem
import functions

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

    # Create interviews
    test_interviews = pd.DataFrame({
        'Time': [],
        'Pledge': [],
        'Brother': [],
        "Quality": [],
    })
    test_interviews.to_csv('interviews.csv', index=False)

    yield
    
    # Cleanup
    for file in ['pledges.csv', 'Points.csv', 'PendingPoints.csv',
                 'pledge_points_graph.png', 'points_over_time.png', "Interviews.csv"]:
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
    df = PointSystem.get_points_csv()
    assert os.path.exists('Points.csv')
    assert list(df.columns) == ["Time", "Name", "Point_Change", "Comments"]
    
    # Test get_pending_points_csv creates file
    df = PointSystem.get_pending_points_csv()
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
    assert CheckRoles.check_pledge("TestPledge1") == True
    assert CheckRoles.check_pledge("NonexistentPledge") == False
    
    # Test getting pledges
    pledges = PointSystem.get_pledges()
    assert "TestPledge1" in pledges
    assert "NewPledge" in pledges
    assert len(pledges) >= 4
    
    # Test deleting pledges
    assert fn.delete_pledge("TestPledge1") == 0
    assert fn.delete_pledge("NonexistentPledge") == 1
    assert not CheckRoles.check_pledge("TestPledge1")

# Test Points System
def test_points_system(setup_test_files):
    """Test points management system"""
    # Test point updates
    assert PointSystem.update_points("TestPledge1", 5, "Test update") == 0
    assert PointSystem.update_points("NonexistentPledge", 5, "Test") == 1
    assert PointSystem.update_points("TestPledge1", "invalid", "Test") == 1
    assert PointSystem.update_points("TestPledge1", 5, "") == 1
    
    # Test point retrieval
    points = PointSystem.get_pledge_points("TestPledge1")
    assert isinstance(points, (int, float, np.integer, np.floating))
    assert points == 15  # 10 from setup + 5 from update
    assert PointSystem.get_pledge_points("NonexistentPledge") is None
    
    # Test point retrieval with df 
    df = PointSystem.get_points_csv()
    points = PointSystem.get_pledge_points("TestPledge1", df)
    assert isinstance(points, (int, float, np.integer, np.floating))
    assert points == 15  # 10 from setup + 5 from update
    assert PointSystem.get_pledge_points("NonexistentPledge") is None
    del df

# Test Pending Points System
def test_pending_points_system(setup_test_files):
    """Test pending points functionality"""
    # Test adding pending points
    assert PointSystem.add_pending_points("TestPledge1", 5, "New pending", "TestBrother") == 0
    assert PointSystem.add_pending_points("NonexistentPledge", 5, "Test", "TestBrother") == 1
    
    # Test approving points
    success, message, data = PointSystem.approve_pending_points(0)
    assert success == True
    assert data['Point_Change'] == 5
    
    # Test rejecting points
    assert PointSystem.add_pending_points("TestPledge2", 5, "Test reject", "TestBrother") == 0
    success, message, data = PointSystem.reject_pending_points(0)
    assert success == True
    assert data['Point_Change'] == 5

# Test Visualization Functions
def test_visualization_functions(setup_test_files):
    """Test graph generation functions"""
    # Test points graph
    graph_file = PointSystem.get_points_graph()
    assert os.path.exists(graph_file)
    assert graph_file.endswith('.png')
    
    # Test points over time
    timeline_file = PointSystem.get_points_over_time()
    assert os.path.exists(timeline_file)
    assert timeline_file.endswith('.png')
    
    # Verify images are valid
    img_points = plt.imread(graph_file)
    img_timeline = plt.imread(timeline_file)
    
    # Test image dimensions and properties
    assert img_points.shape[2] in [3, 4]  # RGB or RGBA
    assert img_timeline.shape[2] in [3, 4]
    assert img_points.shape[0] >= 400  # Height
    assert img_points.shape[1] >= 600  # Width
    assert img_timeline.shape[0] >= 400
    assert img_timeline.shape[1] >= 600
    
    # Clean up
    plt.close('all')

def test_graph_with_no_data(setup_test_files):
    """Test graph generation with empty data"""
    # Create empty Points.csv
    df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
    df.to_csv("Points.csv", index=False)
    
    # Test points graph
    graph_file = PointSystem.get_points_graph()
    assert os.path.exists(graph_file)
    
    # Test timeline graph
    timeline_file = PointSystem.get_points_over_time()
    assert os.path.exists(timeline_file)
    
    # Verify images are valid
    plt.imread(graph_file)
    plt.imread(timeline_file)
    
    # Clean up
    plt.close('all')

@pytest.mark.asyncio
async def test_interactive_plot(setup_test_files):
    """Test generation of interactive plot"""
    # Mock Discord interaction
    mock_interaction = MagicMock()
    mock_interaction.response = MagicMock()
    mock_interaction.response.send_message = AsyncMock()
    
    # Test interactive plot generation
    await fn.interactive_plot(mock_interaction)
    
    # Verify interaction was called
    mock_interaction.response.send_message.assert_called_once()
    
    # Clean up any temporary files
    for file in os.listdir():
        if file.startswith('temp_plot_') and file.endswith('.png'):
            os.remove(file)

def test_graph_updates(setup_test_files):
    """Test that graphs update when data changes"""
    # Generate initial graphs
    initial_points_graph = PointSystem.get_points_graph()
    initial_timeline = PointSystem.get_points_over_time()
    
    # Record initial modification times
    initial_points_mtime = os.path.getmtime(initial_points_graph)
    initial_timeline_mtime = os.path.getmtime(initial_timeline)
    
    # Wait a second to ensure different modification time
    time.sleep(1)
    
    # Add new data
    PointSystem.update_points("TestPledge1", 25, "Test update")
    
    # Generate new graphs
    new_points_graph = PointSystem.get_points_graph()
    new_timeline = PointSystem.get_points_over_time()
    
    # Verify files were updated
    assert os.path.getmtime(new_points_graph) > initial_points_mtime
    assert os.path.getmtime(new_timeline) > initial_timeline_mtime
    
    # Clean up
    plt.close('all')

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
    assert await CheckRoles.check_brother_role(mock_interaction) == True
    
    # Test Brother role absent
    mock_interaction.user.roles = []
    assert await CheckRoles.check_brother_role(mock_interaction) == False
    
    # Test VP Internal role check
    vp_role = MagicMock()
    vp_role.name = "VP Internal"  # Set the role name explicitly
    mock_interaction.guild.roles = [vp_role]
    mock_interaction.user.roles = [vp_role]
    
    # Test VP Internal role present
    assert await CheckRoles.check_vp_internal_role(mock_interaction) == True
    
    # Test VP Internal role absent
    mock_interaction.user.roles = []
    assert await CheckRoles.check_vp_internal_role(mock_interaction) == False

# Test Error Handling
def test_error_handling(setup_test_files):
    """Test error handling in various scenarios"""
    # Test file operations with invalid permissions
    with patch('builtins.open', side_effect=PermissionError):
        df = PointSystem.get_points_csv()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    
    # Test with corrupted files
    with open('Points.csv', 'w') as f:
        f.write("corrupted,data\n")
    df = PointSystem.get_points_csv()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Time", "Name", "Point_Change", "Comments"]

# Test Data Validation
def test_data_validation(setup_test_files):
    """Test input validation functions"""
    # Test point change validation
    assert PointSystem.update_points("TestPledge1", 35, "Valid") == 0
    assert PointSystem.update_points("TestPledge1", -35, "Valid") == 0
    assert PointSystem.update_points("TestPledge1", 36, "Invalid") == 1
    assert PointSystem.update_points("TestPledge1", -36, "Invalid") == 1
    
    # Test comment validation
    long_comment = "x" * 501
    result = PointSystem.update_points("TestPledge1", 5, long_comment)
    assert result == 0
    df = PointSystem.get_points_csv()
    assert len(df.iloc[-1]['Comments']) <= 500


# Test quality and adding interview
def test_interview_fetching(setup_test_files):
    """Test interview fetching functions"""
    # Make sure we get the right number of quality interviews
    assert Interviews.get_quality_interviews("TestPledge1") == 0
    # Make sure that the add_interview function to work
    assert Interviews.add_interview("TestPledge1", "TestBrother2", 1, time.time()) == 0
    # Make sure that the quality interview system works more now
    assert Interviews.get_quality_interviews("TestPledge1") == 1
    assert Interviews.add_interview("TestPledge1", "TestBrother2", "Q", time.time()) == 1
    assert Interviews.add_interview("Hello", "TestBrother2", "Q", time.time()) == 1


@pytest.fixture
def mock_interview_data():
    """Create sample interview data"""
    return pd.DataFrame({
        'Time': [time.time(), time.time() - 3600],
        'Pledge': ['TestPledge1', 'TestPledge2'],
        'Brother': ['Brother1', 'Brother2'],
        'Quality': [1, 0]
    })


# Test Interview System
class TestInterviewSystem:
    def test_get_pledge_interviews(self, setup_test_files):
        """Test getting interviews for a specific pledge"""
        # Test existing pledge
        interviews = Interviews.get_pledge_interviews("TestPledge1")
        assert isinstance(interviews, pd.DataFrame)
        assert 'Quality' in interviews.columns

        # Test non-existent pledge
        result = Interviews.get_pledge_interviews("NonExistentPledge")
        assert result == 1

    def test_get_brother_interviews(self, setup_test_files):
        """Test getting interviews conducted by a brother"""
        # Add test data
        Interviews.add_interview("TestPledge1", "TestBrother", 1, time.time())

        # Test existing brother
        interviews = Interviews.get_brother_interviews("TestBrother")
        assert isinstance(interviews, pd.DataFrame)
        assert not interviews.empty
        assert 'Pledge' in interviews.columns

        # Test brother with no interviews
        empty_interviews = Interviews.get_brother_interviews("InactiveBrother")
        assert isinstance(empty_interviews, pd.DataFrame)
        assert empty_interviews.empty

    def test_interview_rankings(self, setup_test_files, mock_interview_data):
        """Test interview ranking functionality"""
        # Test with provided DataFrame
        rankings = Interviews.interview_rankings(mock_interview_data)
        assert isinstance(rankings, pd.Series)

        # Test with default file reading
        rankings_default = Interviews.interview_rankings()
        assert isinstance(rankings_default, pd.Series) or rankings_default == 1

    def test_interview_summary(self, setup_test_files):
        """Test interview summary generation"""
        # Add test interviews
        current_time = time.time()
        Interviews.add_interview("TestPledge1", "Brother1", 1, current_time)
        Interviews.add_interview("TestPledge1", "Brother2", 0, current_time)
        Interviews.add_interview("TestPledge2", "Brother1", 1, current_time)

        # Test summary generation
        summary = Interviews.interview_summary()
        print(summary)
        assert isinstance(summary, pd.DataFrame)
        assert all(col in summary.columns for col in
                   ["Pledge", "NumberOfInterviews", "PercentQuality", "NQuality"])

        # Verify calculations
        pledge1_row = summary[summary["Pledge"] == "TestPledge1"].iloc[0]
        assert pledge1_row["NumberOfInterviews"] == 2
        assert pledge1_row["NQuality"] == 1
        assert pledge1_row["PercentQuality"] == 50.0

    def test_add_interview_validation(self, setup_test_files):
        """Test input validation for adding interviews"""
        current_time = time.time()

        # Test empty fields
        assert Interviews.add_interview("", "Brother1", 1, current_time) == 1
        assert Interviews.add_interview("TestPledge1", "", 1, current_time) == 1
        assert Interviews.add_interview("TestPledge1", "Brother1", 1, "") == 1

        # Test invalid quality values
        assert Interviews.add_interview("TestPledge1", "Brother1", 2, current_time) == 1
        assert Interviews.add_interview("TestPledge1", "Brother1", -1, current_time) == 1
        assert Interviews.add_interview("TestPledge1", "Brother1", "invalid", current_time) == 1

    def test_brother_interview_rankings(self, setup_test_files):
        """Test brother interview ranking functionality"""
        # Add test data
        current_time = time.time()
        Interviews.add_interview("TestPledge1", "Brother1", 1, current_time)
        Interviews.add_interview("TestPledge2", "Brother1", 0, current_time)
        Interviews.add_interview("TestPledge1", "Brother2", 1, current_time)

        # Test rankings
        rankings = Interviews.brother_interview_rankings()
        assert isinstance(rankings, pd.Series)
        assert "Brother1" in rankings.index.get_level_values('Brother')


# Test Edge Cases and Error Handling
class TestEdgeCases:
    def test_points_system_edge_cases(self, setup_test_files):
        """Test edge cases in points system"""
        # Test floating point values
        assert PointSystem.update_points("TestPledge1", 5.7, "Float test") == 0

        # Test very long names
        assert functions.add_pledge("A" * 50) == 0  # Maximum length
        assert functions.add_pledge("A" * 51) == 1  # Exceeds maximum

        # Test special characters in comments
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert PointSystem.update_points("TestPledge1", 5, special_chars) == 0

        # Test Unicode characters
        unicode_comment = "Test 测试 テスト"
        assert PointSystem.update_points("TestPledge1", 5, unicode_comment) == 0

    def test_concurrent_updates(self, setup_test_files):
        """Test handling of concurrent updates"""
        # Simulate concurrent updates
        results = []
        for i in range(10):
            result = PointSystem.update_points("TestPledge1", 1, f"Concurrent update {i}")
            results.append(result)

        # Verify all updates were successful
        assert all(result == 0 for result in results)

        # Verify final point total is correct
        points = PointSystem.get_pledge_points("TestPledge1")
        assert points == sum(1 for result in results if result == 0) + 10  # +10 from initial setup

    @pytest.mark.asyncio
    async def test_discord_interaction_edge_cases(self):
        """Test edge cases in Discord interactions"""
        # Test with missing roles
        mock_interaction = MagicMock()
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.roles = []
        mock_interaction.response = MagicMock()
        mock_interaction.response.send_message = AsyncMock()

        assert await CheckRoles.check_brother_role(mock_interaction) == False
        assert await CheckRoles.check_vp_internal_role(mock_interaction) == False
