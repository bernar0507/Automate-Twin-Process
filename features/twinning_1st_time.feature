Feature: Twinning Process Performance Testing in Eclipse Ditto

  Scenario: Test twinning process and capture time for 100 iterations
    Given I have a clean environment with Eclipse Ditto set up
    And I will start the first twinning process
    When I initiate the twinning process for 100 iterations
    Then I should have a CSV file with the time data of 100 iterations
