import os.path


def photo_path(avatar_id, extension):
    return os.path.join("photos", "%d.%s" % (avatar_id, extension))


def get_photo_ext(avatar_id, extension):
    try:
        with open(photo_path(avatar_id, extension), "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


async def get_photo(session, avatar_id, image_path):
    return (
        get_photo_ext(avatar_id, "jpeg")
        or get_photo_ext(avatar_id, "png")
        or await download_photo(session, avatar_id, image_path)
    )


async def download_photo(session, avatar_id, image_path):
    print("FETCH: ", image_path)
    async with session.get(image_path) as response:
        image_data = await response.read()

        if response.content_type == "image/jpeg":
            extension = "jpeg"
        elif response.content_type == "image/png":
            extension = "png"

        with open(photo_path(avatar_id, extension), "wb") as fh:
            fh.write(image_data)

    return image_data
