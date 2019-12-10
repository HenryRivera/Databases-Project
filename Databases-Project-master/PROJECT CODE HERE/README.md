Group Members: Brandon Lee, Henry Rivera

Finstagram gives users more privacy than many photo sharing sites by giving them more detailed control over who can see which photos they post. The focus of the project is on storing data about who posted which photos and who has permission to view them, tag others in them, see who’s tagged in what, etc.
 
Features implemented: 
 
MANDATORY:

Login: The user enters her username and password. Finstagram will add “salt” to the password, hash it, and check whether the hash of the password matches the stored password for that email. If so, it initiates a session, storing the username and any other relevant data in session variables, then goes to the home page (or provides some mechanism for the user to select her next action.) If the password does not match the stored password for that username (or no such user exists), Finstagram informs the user that the login failed and does not initiate the session 
 
View visible photos: Finstagram shows the user the photoID and photoPoster of each photo that is visible to her, arranged in reverse chronological order. 

View further photo info: Display the following for visible photos (You may include this with the results of “view visible photos” or you may supply a different way for users to see this additional info, such as clicking on additional links).

  a)	Display the photo or include a link to display it.
  b)	The firstName and lastName of the photoPoster  
  c)	The timestamp,  
  d)	the usernames, first names and last names of people who have been tagged in the photo (taggees), provided that they have       accepted the tags (Tag.acceptedTag == true)  
  e)	The usernames of people who have liked the photo and the rating they gave it
 
Post a photo: User enters

  a.	the location of a photo on their computer,  
  b.	a designation of whether the photo is visible to all followers (allFollowers == true) or only to members of designated         FriendGroups (allFollowers == false). 
Finstagram inserts data about the photo (including current time*, and current user as photoPoster) into the Photo table. Finstagram gives the user a way to designate FriendGroups that the user belongs to with which the Photo is shared. *Finstagram can find the current time with an SQL function or a function in the host language. 

Manage Follows: Brandon will complete Part A and Henry will test. Vice versa will be done for Part B

  a.	User enters the username of someone they want to follow. Finstagram adds an appropriate tuple to Follow, with                 acceptedFollow == False.  
  b.	User sees list of requests others has made to follow them and has the opportunity to accept, by setting acceptFollow to       True or to decline by deleting the request from the Follow table. 

Extra Features Implemented:

•	Like Photo: Brandon implemented this feature and Henry tested

  a.	restricted to liking Photos that are visible to the user 
 
•	Search by poster: Henry implemented this feature and Brandon tested

  a.	Search for photos that are visible to the user and that were posted by some particular person (the user or someone             else)
  
•	Add friendGroup: Henry implemented this feature and Brandon tested

  a.	User provides a name for the group. Finstagram creates the group with current user as the groupOwner, provided that           they don’t already own a group with this name. Gives meaningful error message if the current user already has a group         with this name.
  
•	Add friend: Brandon implemented this feature and Henry tested

  a.	User selects an existing FriendGroup that they own and provides username of someone she’d like to add to the group.           Finstagram checks whether there is exactly one person with that name and updates the Belong table to indicate that the         selected person is now in the FriendGroup. Unusual situation such as the person already being in the group should be           handled gracefully. 

