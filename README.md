# Populate your Google calendar from your [Game Officials](http://www.gameofficials.net) game list.

A simple little program that will log into your GO account and find all your assignments for the current month and the next month.  It will then add those to your Google calendar if they do not already exist.

This saves the hassle of downloading the .ics file and clickty-clickty to import into Google calendar.  Plus you don't miss any.

## Some assembly required

You have to run this the first time and then authorize Google to allow access.  It's easy, and it will create a ~/.credentials directory.  Please refer to Googles documentation at [the Google Python API Quickstart](https://developers.google.com/google-apps/calendar/quickstart/python) for details

This program expects your GO username and GO password to be environment variables.  I did this because eventually I want to run it on Heroku and setting environment variables up is easy.