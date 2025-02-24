def delete_trailing_slash(url:str) -> str:
    while url.endswith('/'):
        url = url[:-1]

    return url