include(../../../build-tools/lvgl.cmake)
include(../../../build-tools/text_to_image.cmake)


if(CONFIG_DISPLAY_DEMO_MODE)
  set(SPLASHSCREEN_VERSION "0.4.0")
  set(SPLASHSCREEN_GIT_HASH "abcd123")
else()
  set(SPLASHSCREEN_VERSION "${APP_VERSION_STRING}")
  execute_process(
    COMMAND git rev-parse --short HEAD
    WORKING_DIRECTORY ${APPLICATION_SOURCE_DIR}/..
    OUTPUT_VARIABLE SPLASHSCREEN_GIT_HASH
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endif()

if(CONFIG_ZMK_DISPLAY AND CONFIG_NICE_VIEW_SNO1_STATUS
  AND (NOT CONFIG_ZMK_SPLIT OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
)

  generate_lvgl_bitmap_fonts(symbol-fonts.h
    FONTS ${CMAKE_CURRENT_SOURCE_DIR}/res/profiles-s.bdf
          ${CMAKE_CURRENT_SOURCE_DIR}/res/profiles-xs.bdf
          ${CMAKE_CURRENT_SOURCE_DIR}/res/indicators.bdf
    NAME "font_{name}"
    )
  generate_lvgl_bitmap_fonts(text-fonts.h
    FONTS ${CMAKE_CURRENT_SOURCE_DIR}/res/ter-u14b-mod.bdf
          ${CMAKE_CURRENT_SOURCE_DIR}/res/ter-u12b-mod.bdf
    RANGES "0x20-0x7e,0xa1-0xff"
    NAME "font_{name}"
  )

  FILE(GLOB icon_pngs
    ${CMAKE_CURRENT_SOURCE_DIR}/res/endpoint*.png
    ${CMAKE_CURRENT_SOURCE_DIR}/res/n*.png 
    ${CMAKE_CURRENT_SOURCE_DIR}/res/battery*.png
  )
  generate_lvgl_indexed_images(widget-icons.h
    MODE "black_white_alpha"
    ROTATE 90
    INVERT ${CONFIG_NICE_VIEW_WIDGET_INVERTED}
    IMAGES ${icon_pngs}
    IMG_NAME "icon_{name}"
    DECLARE_SEQ_STRUCT "img_dsc_seq"
    SEQ_NAME "icons_{name}"
  )

  text_to_image(${CMAKE_CURRENT_BINARY_DIR}/res/app-version.png
    "${SPLASHSCREEN_VERSION}"
    ${CMAKE_CURRENT_SOURCE_DIR}/res/ter-u14b-mod.bdf 2 TRIM
  )
  execute_process(
    COMMAND git rev-parse --short HEAD
    WORKING_DIRECTORY ${APPLICATION_SOURCE_DIR}/..
    OUTPUT_VARIABLE GIT_HASH
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  text_to_image(${CMAKE_CURRENT_BINARY_DIR}/res/git-hash.png
    "${SPLASHSCREEN_GIT_HASH}"
    ${CMAKE_CURRENT_SOURCE_DIR}/res/ter-u12b-mod.bdf 1 TRIM
  )
  FILE(GLOB splashicon_pngs
    ${CMAKE_CURRENT_SOURCE_DIR}/res/splash-logo*.png
  )
  generate_lvgl_indexed_images(splash-icons.h
    MODE "black_white_alpha"
    ROTATE 90
    INVERT ${CONFIG_NICE_VIEW_WIDGET_INVERTED}
    IMAGES ${CMAKE_CURRENT_SOURCE_DIR}/res/splash-title.png
           ${CMAKE_CURRENT_BINARY_DIR}/res/app-version.png
           ${CMAKE_CURRENT_BINARY_DIR}/res/git-hash.png
           ${splashicon_pngs}
    IMG_NAME "icon_{name}"
    DECLARE_SEQ_STRUCT "img_dsc_seq"
    SEQ_NAME "icons_{name}"
  )

  zephyr_library_include_directories(${CMAKE_SOURCE_DIR}/include)

  zephyr_library_sources(src/custom_status_screen.c)
  zephyr_library_sources(src/drawing-util.c)
  zephyr_library_sources(src/widgets.c)

  zephyr_library_sources_ifdef(CONFIG_PRINT_LVGL_SNAPSHOTS src/snapshot.c)

  zephyr_library_sources_ifdef(CONFIG_DISPLAY_DEMO_MODE src/testing.c)

  if(${CONFIG_DISPLAY_DEMO_MODE})
    set(testing_states_py ${CMAKE_CURRENT_SOURCE_DIR}/src/testing_states.py)
    set(testing_states_h ${CMAKE_CURRENT_BINARY_DIR}/testing_states.h)
    add_custom_command(
      OUTPUT ${testing_states_h}
      COMMAND ${PYTHON_EXECUTABLE} ${testing_states_py} --CONFIG_TRACKED_PROFILE_COUNT="${CONFIG_TRACKED_PROFILE_COUNT}"
              > ${testing_states_h}
      DEPENDS ${testing_states_py}
      COMMENT "Generating test cases"
    )
    _add_target(${testing_states_h} sno1)
  endif()

endif()
