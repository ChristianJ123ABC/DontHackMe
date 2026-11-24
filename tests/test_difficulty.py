#Difficulty threshold:
#Easy = 0-39%
#Medium = 40-69%
#Hard = 70%+
#Averages not not rounded (69.9 != hard)

from difficulty import getDifficulty

def testNewUserIsEasy():
    assert getDifficulty([]) == "easy"

def testEasyThreshold():
    assert getDifficulty([0]) == "easy"
    assert getDifficulty([39]) == "easy"
    assert getDifficulty([40]) == "medium"

def testMediumThreshold():
    assert getDifficulty([69]) == "medium"
    assert getDifficulty([70]) == "hard"
    assert getDifficulty([100]) == "hard"

def testAverageThreeScores():
    assert getDifficulty([80,60,40]) == "medium" #Average Score: 60
    assert getDifficulty([100,100,0]) == "medium" #Average Score: 66.7
    assert getDifficulty([100,80,60]) == "hard" #Average Score: 80
    assert getDifficulty([20,20,40]) == "easy" #Average Score: 26.7

def testAverageTwoScores():
    assert getDifficulty([80,20]) == "medium" #Average Score: 50

#The average is not rounded: 69.9 is still medium
def testAverageIsNotRounded():
    assert getDifficulty([69.9]) == "medium"