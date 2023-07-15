Feature: Performance Testing of Eclipse Ditto for 10 iWatch

  Scenario: Twinning and performance testing for ten iWatch
    Given I have a clean environment
    When I start the twinning process for 10 iWatch
    Then I measure and record the performance for 30 minutes
