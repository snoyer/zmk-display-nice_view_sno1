
#pragma once
#include <lvgl.h>
#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif


#ifndef LV_ATTRIBUTE_IMG_IMG_A1
#define LV_ATTRIBUTE_IMG_IMG_A1
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_IMG_A1 uint8_t img_a1_map[] = {
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0x00,
};
const lv_img_dsc_t img_a1 = {
#if LVGL_VERSION_MAJOR >= 9
  .header.cf = LV_COLOR_FORMAT_I1,
#else
  .header.cf = LV_IMG_CF_INDEXED_1BIT,
  .header.always_zero = 0,
  .header.reserved = 0,
#endif
  .header.w = 3,
  .header.h = 1,
  .data_size = 9,
  .data = img_a1_map,
};


#ifndef LV_ATTRIBUTE_IMG_IMG_A2
#define LV_ATTRIBUTE_IMG_IMG_A2
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_IMG_A2 uint8_t img_a2_map[] = {
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0xff, 0x00, 0x00, 0xff, /* color #1 */
  0x40,
};
const lv_img_dsc_t img_a2 = {
#if LVGL_VERSION_MAJOR >= 9
  .header.cf = LV_COLOR_FORMAT_I1,
#else
  .header.cf = LV_IMG_CF_INDEXED_1BIT,
  .header.always_zero = 0,
  .header.reserved = 0,
#endif
  .header.w = 3,
  .header.h = 1,
  .data_size = 9,
  .data = img_a2_map,
};

const struct img_list_t imgs_a = {2, {
  &img_a1,
  &img_a2,
}};
