#pragma once
#include "lvgl.h"

/* font_test_font (from test-font.bdf) */

static LV_ATTRIBUTE_LARGE_CONST const uint8_t font_test_font_glyph_bitmap[] = {
  /* u0063 'c' */
  0xc0,
  /* u0064 'd' */
  0xd0,
  /* u0065 'e' */
  0x90,
  /* u0066 'f' */
  0xe0,
  /* u0067 'g' */
  0xf0,
  /* u0069 'i' */
  0x60,
  /* u006A 'j' */
  0x70,
  /* u006D 'm' */
  0xc8,
  /* u006F 'o' */
  0x98,
  /* u0071 'q' */
  0xf8,
  /* u0075 'u' */
  0x8c,
  /* u0076 'v' */
  0xac,
  /* u0077 'w' */
  0x74,
  /* u0078 'x' */
  0xcc,
  /* u0079 'y' */
  0xdc,
};
static const lv_font_fmt_txt_glyph_dsc_t font_test_font_glyph_dsc[] = {
  {.bitmap_index=   0, .adv_w=  0, .box_w= 0, .box_h= 0, .ofs_x= 0, .ofs_y= 0} /* reserved */,
  {.bitmap_index=   0, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0063 'c' */,
  {.bitmap_index=   1, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0064 'd' */,
  {.bitmap_index=   2, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0065 'e' */,
  {.bitmap_index=   3, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0066 'f' */,
  {.bitmap_index=   4, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0067 'g' */,
  {.bitmap_index=   5, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0069 'i' */,
  {.bitmap_index=   6, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u006A 'j' */,
  {.bitmap_index=   7, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u006D 'm' */,
  {.bitmap_index=   8, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u006F 'o' */,
  {.bitmap_index=   9, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0071 'q' */,
  {.bitmap_index=  10, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0075 'u' */,
  {.bitmap_index=  11, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0076 'v' */,
  {.bitmap_index=  12, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0077 'w' */,
  {.bitmap_index=  13, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0078 'x' */,
  {.bitmap_index=  14, .adv_w= 32, .box_w= 2, .box_h= 3, .ofs_x= 0, .ofs_y= 0} /* u0079 'y' */,
};

static const uint16_t font_test_font_unicode_list_2[] = { 0x006D -109, 0x006F -109, 0x0071 -109 };
static const lv_font_fmt_txt_cmap_t font_test_font_cmaps[] = {
  {.range_start = 0x0063, .range_length = 5, .glyph_id_start = 1,
   .unicode_list = NULL, .glyph_id_ofs_list = NULL, .list_length = 0,
   .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY},
  {.range_start = 0x0069, .range_length = 2, .glyph_id_start = 6,
   .unicode_list = NULL, .glyph_id_ofs_list = NULL, .list_length = 0,
   .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY},
  {.range_start = 0x006D, .range_length = 5, .glyph_id_start = 8,
   .unicode_list = font_test_font_unicode_list_2, .glyph_id_ofs_list = NULL, .list_length = 3,
   .type = LV_FONT_FMT_TXT_CMAP_SPARSE_TINY},
  {.range_start = 0x0075, .range_length = 5, .glyph_id_start = 11,
   .unicode_list = NULL, .glyph_id_ofs_list = NULL, .list_length = 0,
   .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY},
};

#if LVGL_VERSION_MAJOR == 8
static lv_font_fmt_txt_glyph_cache_t font_test_font_cache;
#endif
#if LVGL_VERSION_MAJOR >= 8
static const lv_font_fmt_txt_dsc_t font_test_font_font_dsc = {
#else
static lv_font_fmt_txt_dsc_t font_test_font_font_dsc = {
#endif
  .glyph_bitmap = font_test_font_glyph_bitmap,
  .glyph_dsc = font_test_font_glyph_dsc,
  .cmaps = font_test_font_cmaps,
  .cmap_num = 4,
  .kern_dsc = NULL,
  .kern_scale = 0,
  .bpp = 1,
  .kern_classes = 0,
  .bitmap_format = 0,
#if LVGL_VERSION_MAJOR == 8
  .cache = &font_test_font_cache
#endif
};

#if LVGL_VERSION_MAJOR >= 8
const lv_font_t font_test_font = {
#else
lv_font_t font_test_font = {
#endif
  .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,
  .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,
  .line_height = 3,
  .base_line = 0,
#if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
  .subpx = LV_FONT_SUBPX_NONE,
#endif
#if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
  .underline_position = -1,
  .underline_thickness = 1,
#endif
  .dsc = &font_test_font_font_dsc,
#if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
  .fallback = NULL,
#endif
  .user_data = NULL,
};

