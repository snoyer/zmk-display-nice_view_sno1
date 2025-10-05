function(text_to_image img_file text font spacing)
  add_custom_command(
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/text_to_image.py
            ${font} --text="${text}" -o ${img_file} -s ${spacing}
    DEPENDS ${font}
    OUTPUT ${img_file}
    COMMENT "Generating ${img_file} for `${text}`"
  )
  _add_target(${img_file} text_to_image)
endfunction()
