function(text_to_image img_file text font spacing)
  cmake_parse_arguments(TEXT_TO_IMAGE "TRIM" "" "" ${ARGN})
  if(TEXT_TO_IMAGE_TRIM)
    list(APPEND TEXT_TO_IMAGE_TRIM_PY_ARGS "-t" ${TEXT_TO_IMAGE_TRIM_PY_ARGS})
  endif()
  add_custom_command(
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/text_to_image.py
            ${font} --text="${text}" -o ${img_file} -s ${spacing} ${TEXT_TO_IMAGE_TRIM_PY_ARGS}
    DEPENDS ${font}
    OUTPUT ${img_file}
    COMMENT "Generating ${img_file} for `${text}`"
  )
  _add_target(${img_file} text_to_image)
endfunction()
