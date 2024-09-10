<?php


if (isset($_POST['send'])) {
    $name = $_POST['name'];
    $country = $_POST['country'];
    $phone = $_POST['phone'];
    $email = $_POST['email'];
    $subject = $_POST['message'];

    // Check if the 'options' field is set, and if so, use it; otherwise, set it to an empty string
    // $options = isset($_POST['option']) ? implode(', ', $_POST['option']) : '';

    // $to = 'info@ramonhomestay.com'; 
    $to = 'consult@datapkt.com'; 
    $headers = "From: $email";

    $email_content = "Name: $name\n";
    $email_content .= "Country: $country\n";
    $email_content .= "Phone: $phone\n";
    $email_content .= "Email: $email\n";
    // $email_content .= "Subject:  $subject\n";
    $email_content .= "Message:\n$subject";

    if (mail($to, "Form Submission", $email_content, $headers)) {
        // JavaScript alert
        echo '<script>alert("Your message was sent successfully!");</script>';
        
        // JavaScript redirect to the home page
        echo '<script>window.location.replace("https://www.datapktaviation.com");</script>';
        exit;
    } else {
        echo "Failed to send email.";
    }
}
?>
