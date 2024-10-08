import numpy as np
import mysql.connector

class AdaptiveLearningModel:
    def __init__(self, subjects, topics, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1):
        self.subjects = subjects
        self.topics = topics
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table = {subject: np.zeros((11, 3)) for subject in subjects}
        try:
            self.db_connection = mysql.connector.connect(
                host ="localhost",
                user="root",
                password="",
                database="capstone"
            )
            self.cursor = self.db_connection.cursor()
        except mysql.connector.Error as err:
            print("Error connecting to MySQL:", err)

    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()


    def choose_action(self, subject, mcq_score, topic):
        mcq_score_index = min(max(0, mcq_score), 10)  # Ensure MCQ score index is within range [0, 10]
        if np.random.uniform(0, 1) < self.exploration_rate:
            return np.random.choice(3)  # Explore: choose a random action
        else:
            return np.argmax(self.q_table[subject][mcq_score_index])

    def update_q_table(self, subject, mcq_score, action, reward, next_mcq_score, next_action, topic):
        mcq_score_index = min(max(0, mcq_score), 10)  
        next_mcq_score_index = min(max(0, next_mcq_score), 10)  
        old_value = self.q_table[subject][mcq_score_index][action]
        future_action_value = self.q_table[subject][next_mcq_score_index][next_action]
        new_value = old_value + self.learning_rate * (reward + self.discount_factor * future_action_value - old_value)
        self.q_table[subject][mcq_score_index][action] = new_value

    def determine_level(self, mcq_score):
        # Define level thresholds with 'beginner' mapped to 0
        level_thresholds = {
            '1': 0,
            '2': 5,
            '3': 8
        }
        
        # Determine the level based on the MCQ score
        for level, threshold in level_thresholds.items():
            if mcq_score >= threshold:
                return level
        
        # Default to beginner if score doesn't meet any thresholds
        return '1'

    def train(self, user_id, subject, mcq_score, action, reward, next_mcq_score, next_action, topic):
        self.update_q_table(subject, mcq_score, action, reward, next_mcq_score, next_action, topic)
        # Determine level based on the next MCQ score
        next_level = self.determine_level(next_mcq_score)
        # Update the MySQL database with the next level
        sql = "UPDATE scores SET SubjectScore = %s, TopicScore = %s, Level = %s WHERE UserId = %s AND Subject = %s AND Topic = %s"
        val = (next_mcq_score, next_action, next_level, user_id, subject, topic)
        self.cursor.execute(sql, val)
        self.db_connection.commit()

    def test(self, subject, mcq_score, topic):
        mcq_score_index = min(max(0, mcq_score), 10)  
        return np.argmax(self.q_table[subject][mcq_score_index])

    def __del__(self):
        self.cursor.close()
        self.db_connection.close()


#----------------------------------------------
# TEST BELOW  
#-----------------------------------------------    

# if __name__ == "__main__":
#     # Initialize subjects and topics
#     subjects = ['Biology']
#     topics = ['']  # Assuming topics for each subject

#     # Create an instance of AdaptiveLearningModel
#     adaptive_model = AdaptiveLearningModel(subjects, topics)

#     # Example usage of train method
#     user_id = 1
#     subject = 'Biology'
#     mcq_score = 7
#     action = 0
#     reward = 1
#     next_mcq_score = 8
#     next_action = 1
#     topic = 'Algebra'
#     adaptive_model.train(user_id, subject, mcq_score, action, reward, next_mcq_score, next_action, topic)
