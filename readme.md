# **News Comment and Favorites App**



This app allows users to click on links to news sites, read stories, and interact with articles by leaving comments, liking other users' comments, and creating a list of favorite articles. Unfortunately this can only be run on the local server with the API key that is provided.  The company changed their policy and no longer allows the free keys to be used in production. I have included a sample .env folder. You would need to add your API_KEY, SECRET_KEY, DATABASE_URL.
## **Features**

- **Comment on Articles:** Users can comment on articles that normally lack a comment section on the source website.
- **Like Comments:** Users can like other users' comments, encouraging engagement and discussion.
- **Favorite Articles:** Articles can be saved to a user's favorite list for easy reference later.
- **User Profiles:** Users can click on another user's profile to see the articles they have liked or favorited.

## **Technology Stack**

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **Database:** PostgreSQL
- **Authentication:** `Flask-Login` for user authentication and session management.

## **Key Decisions**

### **JavaScript for Interaction**
I chose JavaScript to handle the favorite and like buttons because it allows for real-time updates without requiring a page refresh. When a user interacts with these buttons, the UI updates immediately via JavaScript, and the state is saved using an AJAX request.

### **Flask-Login for Authentication**
I used `Flask-Login` to manage user authentication. `Flask-Login` streamlines the process of logging in, handling sessions, and keeping the codebase clean and easy to manage.

## **How It Works**

1. **Sign Up or Log In:** The user creates an account or logs in to their existing account.
2. **View Articles:** Once logged in, the app displays a list of top news articles from various authors. Users can click on the article titles to read the full articles.
3. **Interact with Articles:**
   - **Favorite:** After reading an article, users can return to the main page and click **Favorite** to save it in their personal list.
   - **Comment:** Users can leave a comment on the article.
   - **Like Comments:** Users can like other users' comments to show appreciation.
4. **View Favorites and Liked Comments:** A user can view their favorite articles or click on another user's profile to see their liked articles and comments.
5. **Sign Out:** The user can log out once they are done interacting with the app.

## **Challenges**

I encountered difficulties in integrating the API for news articles, as the API database did not provide unique IDs for each article. To work around this, I had to create unique instances of articles in my own database when users interacted with an article (e.g., favoriting or commenting on it).
