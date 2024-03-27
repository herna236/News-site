with this app you are able to click on links to newsites and read stories that do not neccisarily have a comment section.
my app allows users to comment on the articles, like other users comments, and have a list of favorite articles.

The title of my site is arhnews. it is deployed at https://mycapstone1.onrender.com/

I used javaScript to handle the favorite buttons and like buttons.  I chose this becuase it doesnt require a page
refresh.  the change is reflected on the button and JS and an AJAX request. 
I chose to use flask_login to handle my user login and authication.  I used this becuase it really streamlines the code and makes
 it easy to use.

so you would sign up for an account or login. the page refreshes and you are shown the top news articles from various authors.  
you can click the titles to read the articles. then you woul have to hit the back arrow and click favorite or comments.  when you 
do that the article is saved in the database and any favorties or comments can be saved with the article.  a user can like another users comment and click
on the users username to see the users liked articles. the user would sign out.

html, python, flask, postgresql, HTML, CSS JavaScript are used in my application


I struggled figuring out how to manipulate this api becuase the articles in the api db do not have
an id for each article.  I had to figure out how to create instances of articles in my db when a user
interacted with the article (favorite, comments)