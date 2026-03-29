
function(_add_target generated_file prefix)
  # add the generated file's parent directory to the include search path
  zephyr_library_include_directories(${CMAKE_CURRENT_BINARY_DIR})

  # create a target so that the command is called at build-time
  # (not sure this is the best way to do it but it works)
  get_filename_component(GENERATED_TARGET_NAME ${generated_file} NAME_WE)
  set(GENERATED_TARGET_NAME ${prefix}_${GENERATED_TARGET_NAME})
  add_custom_target(${GENERATED_TARGET_NAME} DEPENDS ${generated_file})
  add_dependencies(${ZEPHYR_CURRENT_LIBRARY} ${GENERATED_TARGET_NAME})
endfunction()


function(generate_lvgl_bitmap_fonts header_filename)
  cmake_parse_arguments(GENERATE_LVGL_BITMAP_FONTS "" "RANGES;NAME" "FONTS" ${ARGN})
  set(GENERATED_FILE ${CMAKE_CURRENT_BINARY_DIR}/${header_filename})

  # build python command arguments from cmake function arguments
  if(GENERATE_LVGL_BITMAP_FONTS_RANGES)
    list(APPEND GENERATE_LVGL_BITMAP_FONTS_PY_ARGS "--ranges" ${GENERATE_LVGL_BITMAP_FONTS_RANGES})
  endif()
  if(GENERATE_LVGL_BITMAP_FONTS_NAME)
    list(APPEND GENERATE_LVGL_BITMAP_FONTS_PY_ARGS "--name" ${GENERATE_LVGL_BITMAP_FONTS_NAME})
  endif()

  add_custom_command(
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/lvgl_bitmap_font.py
            ${GENERATE_LVGL_BITMAP_FONTS_FONTS}
            --output ${GENERATED_FILE}
            ${GENERATE_LVGL_BITMAP_FONTS_PY_ARGS}
    DEPENDS ${GENERATE_LVGL_BITMAP_FONTS_FONTS}
    OUTPUT ${GENERATED_FILE}
    COMMENT "Generating LVGL bitmap font(s) code to ${header_filename}"
  )

  _add_target(${GENERATED_FILE} lvgl_bitmap_font)
endfunction()


function(generate_lvgl_indexed_images header_filename) 
  cmake_parse_arguments(GENERATE_LVGL_INDEXED_IMAGES "" "ROTATE;INVERT;IMG_NAME;DECLARE_SEQ_STRUCT;USE_SEQ_STRUCT;SEQ_NAME" "IMAGES" ${ARGN})
  set(GENERATED_FILE ${CMAKE_CURRENT_BINARY_DIR}/${header_filename})

  # build python command arguments from cmake function arguments
  if(GENERATE_LVGL_INDEXED_IMAGES_ROTATE)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--rotate" ${GENERATE_LVGL_INDEXED_IMAGES_ROTATE})
  endif()
  if(GENERATE_LVGL_INDEXED_IMAGES_INVERT)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--invert")
  endif()
  if(GENERATE_LVGL_INDEXED_IMAGES_IMG_NAME)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--img-name" ${GENERATE_LVGL_INDEXED_IMAGES_IMG_NAME})
  endif()
  if(GENERATE_LVGL_INDEXED_IMAGES_DECLARE_SEQ_STRUCT)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--declare-seq-struct" ${GENERATE_LVGL_INDEXED_IMAGES_DECLARE_SEQ_STRUCT})
  endif()
  if(GENERATE_LVGL_INDEXED_IMAGES_DECLARE_USE_SEQ_STRUCT)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--use-seq-struct" ${GENERATE_LVGL_INDEXED_IMAGES_DECLARE_USE_SEQ_STRUCT})
  endif()
  if(GENERATE_LVGL_INDEXED_IMAGES_SEQ_NAME)
    list(APPEND GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS "--seq-name" ${GENERATE_LVGL_INDEXED_IMAGES_SEQ_NAME})
  endif()
  add_custom_command(
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/lvgl_indexed_image.py
            ${GENERATE_LVGL_INDEXED_IMAGES_IMAGES}
            --output ${GENERATED_FILE}
            ${GENERATE_LVGL_INDEXED_IMAGES_PY_ARGS}
    DEPENDS ${GENERATE_LVGL_INDEXED_IMAGES_IMAGES}
    OUTPUT ${GENERATED_FILE}
    COMMENT "Generating LVGL indexed image(s) code to ${GENERATED_FILE} from images"
  )

  _add_target(${GENERATED_FILE} lvgl_imgs)
endfunction()

