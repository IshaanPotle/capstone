<!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Register</title>
        <link rel="shortcut icon" href="{{ url_for('static', filename='images/fav.png') }}" type="image/x-icon">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&amp;display=swap" rel="stylesheet">
        <link rel="shortcut icon" href="{{ url_for('static', filename='images/fav.jpg') }}">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
        <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='css/style1.css') }}" />

    </head>
    <body class="bg-white">
        <div class="container-fluid vh-100">
            <div class="row vh-100 ">
                <div class="col-lg-6 bg-gray p-5 text-center">
                   <p class="mb-3 fs-7">Already have an account ?</p>
                   <a href="{{ url_for('login') }}"><button class="btn fw-bold mb-5 btn-outline-success px-4 rounded-pill">Log In</button></a>
                   <div class="img-cover p-4">
                    <img src="{{ url_for('static', filename='images/loginbg.svg') }}" alt="">
                   </div>
                </div>
                <div class="col-lg-6 p  vh-100">
                   <div class="row d-flex vh-100">
                   <form method="POST" action="/register">
    <div class="col-md-8 p-4 ikigui m-auto text-center align-items-center">
        <h4 class="text-center fw-bolder mb-4 fs-2">Signup</h4>
        <div class="input-group mb-4">
            <span class="input-group-text border-end-0 inbg" id="basic-addon1"><i class="bi bi-envelope"></i></span>
            <input type="text" class="form-control ps-2 border-start-0 fs-7 inbg form-control-lg mb-0" placeholder="Enter Email Address" aria-label="Email" aria-describedby="basic-addon1" name="email">
        </div>
        <div class="input-group mb-4">
            <span class="input-group-text border-end-0 inbg" id="basic-addon1"><i class="bi bi-lock"></i></span>
            <input type="password" class="form-control ps-2 fs-7 border-start-0 form-control-lg inbg mb-0" placeholder="Enter Password" aria-label="Password" aria-describedby="basic-addon1" name="password">
        </div>
        <button type="submit" class="btn btn-lg fw-bold fs-7 btn-success w-100">Register</button>
    </div>
</form>


                           <p class="text-center py-4 fw-bold fs-8">Or Sign in with social platforms</p>

                           <ul class="d-inline-block mx-auto">
                               <li class="float-start px-3"><a href=""><i class="bi bi-facebook"></i></a></li>
                               <li class="float-start px-3"><a href=""><i class="bi bi-twitter"></i></a></li>
                               <li class="float-start px-3"><a href=""><i class="bi bi-linkedin"></i></a></li>
                               <li class="float-start px-3"><a href=""><i class="bi bi-google"></i></a></li>

                           </ul>
                       </div>
                   </div>

                </div>
            </div>
        </div>
    </body>
    <script src="{{ url_for('static', filename='js/jquery1-3.2.1.min.js')}}"></script>
<script src="{{ url_for('static', filename='js/popper.min.js')}}"></script>
<script src="{{ url_for('static', filename='js/bootstrap1.bundle.min.js')}}"></script>
<script src="{{ url_for('static', filename='plugins/scroll-fixed/jquery-scrolltofixed-min.js')}}"></script>
<script src="{{ url_for('static', filename='plugins/testimonial/js/owl.carousel.min.js')}}"></script>
<script src="{{ url_for('static', filename='js/script1.js')}}"></script>
</html>