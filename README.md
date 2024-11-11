# X engagement tracker

## How to use

1. Clone the repository
2. Install the dependencies using `pip install -r requirements.txt`
3. Set the environment variables in the .env file
4. Run the script using `python main.py`
5. The output data will be saved in the csv file.

## Engagement requirements: The user who is expected to be engaged in the post has to comment on the post and also post on each commenter's pinned post. Eg I am checking the engagement of @the_real_shahrukh, so he has to comment on the post, after commenting on the post he sees that user @the_other_user has also commented he will go inside @the_other_user profile and comment on his pinned post that will be considered as engagement of @the_real_shahrukh for @the_other_user.

## How do we manually check the angagement (if we are not using this script):

1. We open the post url in the browser, scroll to the bottom and note down all the users who commented.
2. Now we go to each commenter's profile and check if the commenter has posted on all other commenter's pinned posts. If yes, then the engagement is successful. Otherwise not.

## The script will also work the same way and provide the result in the following format:

| username | commenter_32 | commenter_53 | commenter_71 | False_count |
| -------- | ------------- | ------------- | ------------- | ------------- |
| the_real_shahrukh | True | True | False | 1 |
| user_abc | False | True | True | 2 |

The above result means that the user the_real_shahrukh has engaged with commenter_32 and commenter_53, but not with commenter_71. So the False_count is 1. the_real_shahrukh has commented on the main post also on the commenter_32's and commenter_53's pinned post but not on commenter_71's pinned post.
