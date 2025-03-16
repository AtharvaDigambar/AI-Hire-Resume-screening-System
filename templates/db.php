<?php
$servername = "localhost";
$username = "root";  // Change if using a different user
$password = "";      // Keep empty if no password is set
$database = "aihire";

// Create a connection
$conn = new mysqli($servername, $username, $password, $database);

// Check the connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
