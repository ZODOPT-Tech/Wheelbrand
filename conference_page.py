def conference_main(request):
    """
    The main handler function for the /conference route.
    This function must be named 'conference_main' exactly, as specified in main.py.
    """
    # A simple example of content returned by the page handler
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Conference Details</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; background-color: #f4f7f6; }}
                h1 {{ color: #007bff; }}
                p {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Welcome to the Wheelbrand Annual Conference</h1>
            <p>This content was loaded successfully by the '{__name__}.{conference_main.__name__}' function.</p>
            <p>Request Path: {request.get('path', '/')}</p>
        </body>
        </html>
    """

# If you had accidentally named it something else (e.g., conference_page), 
# the AttributeError would occur because the router is looking for 'conference_main'.
# def conference_page(request):
#     return "This function is here, but the router can't find it!"
