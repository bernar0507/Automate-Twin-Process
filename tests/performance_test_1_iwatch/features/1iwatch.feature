Feature: Performance Testing of Eclipse Ditto for 1 iWatch

  Scenario: Twinning and performance testing for one iWatch
    Given I have a clean environment
    When I start the twinning process for 1 iWatch
    Then I measure and record the performance for 30 minutes
