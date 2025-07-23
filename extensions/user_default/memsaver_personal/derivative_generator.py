# copyright (c) 2018- polygoniq xyz s.r.o.

import enum
import os
import sys
import logging

logger = logging.getLogger(f"polygoniq.{__name__}")


GENERATORS = []


class GenerateDerivativeResult(enum.Enum):
    UP_TO_DATE = 0  # Derivative is already up to date
    REGENERATED = 1  # Derivative was successfully generated
    REFUSE_UPSCALE = 2  # Refused to generate derivative because original is smaller than side_size
    UNSUPPORTED = 3  # Derivative generation is not supported for this image format
    ERROR = 4  # Derivative generation failed due to an error

    def is_success(self) -> bool:
        """Returns True if the result indicates a valid derivative,
        i.e. UP_TO_DATE or REGENERATED
        """
        return (
            self == GenerateDerivativeResult.UP_TO_DATE
            or self == GenerateDerivativeResult.REGENERATED
        )


try:
    # OpenImageIO is installed by default in Blender 3.5+
    import OpenImageIO as oiio

    def generate_derivative_OIIO(
        original_abs_path: str, derivative_path: str, side_size: int
    ) -> GenerateDerivativeResult:
        _, original_ext = os.path.splitext(original_abs_path)
        _, derivative_ext = os.path.splitext(derivative_path)
        assert original_ext == derivative_ext

        # TODO: More extensions?
        # TODO: Update faq.md in docs when adding new extensions
        if original_ext.lower() not in {
            ".bmp",
            ".exr",
            ".jpg",
            ".jpeg",
            ".jpe",
            ".jif",
            ".jfif",
            ".png",
            ".tga",
            ".hdr",
            ".tiff",
            ".tif",
            ".webp",
        }:
            logger.warning(
                f"Can't generate derivative of {original_abs_path} because its extension "
                f"{original_ext} is not supported by OpenImageIO."
            )
            return GenerateDerivativeResult.UNSUPPORTED

        try:
            original_image = oiio.ImageInput.open(original_abs_path)
            if original_image is None:
                raise RuntimeError(
                    f"OIIO returned None when trying to load {original_abs_path}. "
                    f"OIIO error: {oiio.geterror()}"
                )
            original_spec = original_image.spec()
        except:
            logger.exception(
                f"Uncaught exception while loading {original_abs_path} image with OpenImageIO"
            )
            return GenerateDerivativeResult.ERROR

        original_width = original_spec.width
        original_height = original_spec.height
        if side_size >= original_width and side_size >= original_height:
            logger.warning(
                f"Refused to generate derivative of {original_abs_path} of side size {side_size} "
                f"because the original size {original_width}x{original_height} is smaller or equal!"
            )
            return GenerateDerivativeResult.REFUSE_UPSCALE

        # Compute the new dimensions while maintaining aspect ratio
        if original_width >= original_height:
            new_width = side_size
            new_height = int(side_size * original_height / original_width)
        else:
            new_height = side_size
            new_width = int(side_size * original_width / original_height)

        try:
            derivative_spec = oiio.ImageSpec(
                new_width, new_height, original_spec.nchannels, original_spec.format
            )
            icc_profile = original_spec.get_string_attribute("ICCProfile")
            if icc_profile != "":
                derivative_spec.attribute("ICCProfile", oiio.TypeDesc.TypeString, icc_profile)
            original_buf = oiio.ImageBuf(original_abs_path)
            derivative_buf = oiio.ImageBuf(derivative_spec)
            oiio.ImageBufAlgo.resize(derivative_buf, original_buf, filtername="lanczos3")
            derivative_buf.write(derivative_path)
        except:
            logger.exception(
                f"Uncaught exception while generating derivative for {original_abs_path} "
                f"with OpenImageIO. OIIO error: {oiio.geterror()}"
            )
            return GenerateDerivativeResult.ERROR

        logger.info(
            f"Generated derivative of size {new_width}x{new_height} from original "
            f"{original_abs_path} using OpenImageIO"
        )
        return GenerateDerivativeResult.REGENERATED

    GENERATORS.append(generate_derivative_OIIO)
    logger.info("OpenImageIO successfully imported and will be used for memsaver.")
except ImportError:
    logger.info("OpenImageIO could not be imported, we can't use it for memsaver.")


if len(GENERATORS) == 0:  # We will only try to use PIL/Pillow if OpenImageIO is not present
    try:
        # Install modules which are not in Blender python by default
        # https://conference.blender.org/2022/presentations/1405/
        # or change to this: https://blender.stackexchange.com/questions/168448/bundling-python-library-with-addon
        try:
            import PIL.Image
        except ModuleNotFoundError as ex:
            import subprocess

            python_exe = sys.executable
            args = [python_exe, "-m", "ensurepip", "--upgrade", "--default-pip"]
            if subprocess.call(args=args) != 0:
                raise RuntimeError("Couldn't ensure pip in Blender's python!")
            args = [python_exe, "-m", "pip", "install", "--upgrade", "Pillow"]
            if subprocess.call(args=args) != 0:
                raise RuntimeError("Couldn't install Pillow module in Blender's python!")
            import PIL.Image

        def generate_derivative_PIL(
            original_abs_path: str, derivative_path: str, side_size: int
        ) -> GenerateDerivativeResult:
            _, original_ext = os.path.splitext(original_abs_path)
            _, derivative_ext = os.path.splitext(derivative_path)
            assert original_ext == derivative_ext

            # TODO: More extensions?
            # TODO: Update faq.md in docs when adding new extensions
            if original_ext.lower() not in {
                ".bmp",
                ".jpg",
                ".jpeg",
                ".jpe",
                ".jif",
                ".jfif",
                ".png",
                ".tga",
                ".tiff",
                ".tif",
                ".webp",
            }:
                logger.warning(
                    f"Can't generate derivative of {original_abs_path} because its extension "
                    f"{original_ext} is not supported by PIL."
                )
                return GenerateDerivativeResult.UNSUPPORTED

            try:
                original_image = PIL.Image.open(original_abs_path)
            except:
                logger.exception(
                    f"Uncaught exception while loading {original_abs_path} image with PIL"
                )
                return GenerateDerivativeResult.ERROR

            original_width, original_height = original_image.size
            if side_size >= original_width and side_size >= original_height:
                logger.warning(
                    f"Refused to generate derivative of {original_abs_path} of side size {side_size} "
                    f"because the original size {original_width}x{original_height} is smaller or equal!"
                )
                return GenerateDerivativeResult.REFUSE_UPSCALE

            derivative_image = original_image.copy()
            # thumbnail() creates image no larger than side_size while keeping original aspect ratio
            derivative_image.thumbnail((side_size, side_size), PIL.Image.Resampling.LANCZOS)
            derivative_image.save(
                derivative_path, icc_profile=original_image.info.get("icc_profile", b"")
            )
            logger.info(
                f"Generated derivative of size {side_size} from original {original_abs_path} using PIL"
            )
            return GenerateDerivativeResult.SUCCESS

        GENERATORS.append(generate_derivative_PIL)
        logger.info("PIL/Pillow successfully imported and will be used for memsaver.")
    except ImportError:
        logger.error("PIL/Pillow could not be imported, we can't use it for memsaver.")


if len(GENERATORS) == 0:
    logger.error("No generators available, memsaver won't be able to create derivative images!")


def is_derivative_stale(original_abs_path: str, derivative_path: str) -> bool:
    """Returns True if derivative image does not exist or the original image has changed"""
    if not os.path.isfile(derivative_path):
        logger.info(f"Derivative at path {derivative_path} is stale because it doesn't exist!")
        return True  # doesn't exist, must be stale

    # derivative has been modified earlier than original, must be stale
    if os.path.getmtime(derivative_path) <= os.path.getmtime(original_abs_path):
        logger.info(
            f"Derivative at path {derivative_path} is stale because the original "
            f"{original_abs_path} has a newer modified date!"
        )
        return True

    logger.info(
        f"Derivative at path {derivative_path} is up to date, original at {original_abs_path}."
    )
    return False


def generate_derivative(
    original_abs_path: str, derivative_path: str, side_size: int
) -> GenerateDerivativeResult:
    assert side_size > 0
    logger.info(
        f"Asked to generate derivative of size {side_size} from original {original_abs_path}"
    )

    if not is_derivative_stale(original_abs_path, derivative_path):
        logger.info(
            f"Derivative {derivative_path} of size {side_size} from original {original_abs_path} "
            "is up to date, no need to re-generate."
        )
        return GenerateDerivativeResult.UP_TO_DATE

    if os.path.isfile(derivative_path):
        os.unlink(derivative_path)

    error = False
    for generator in GENERATORS:
        generator_result = generator(original_abs_path, derivative_path, side_size)
        if (
            generator_result == GenerateDerivativeResult.UP_TO_DATE
            or generator_result == GenerateDerivativeResult.REGENERATED
            or generator_result == GenerateDerivativeResult.REFUSE_UPSCALE
        ):
            # Return immediately if the generator didn't fail
            return generator_result
        elif generator_result == GenerateDerivativeResult.ERROR:
            error = True

    if error:
        # There is at least one generator supporting the image format but it failed
        return GenerateDerivativeResult.ERROR
    # No error => No generator supported the image format
    return GenerateDerivativeResult.UNSUPPORTED


def is_generator_available() -> bool:
    return len(GENERATORS) > 0
