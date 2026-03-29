
#pragma once
#include <lvgl.h>
#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif


#ifndef LV_ATTRIBUTE_IMG_FRAME_A1
#define LV_ATTRIBUTE_IMG_FRAME_A1
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_FRAME_A1 uint8_t frame_a1_map[] = {
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0x00,
};
const lv_img_dsc_t frame_a1 = {
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
  .data = frame_a1_map,
};


#ifndef LV_ATTRIBUTE_IMG_FRAME_A2
#define LV_ATTRIBUTE_IMG_FRAME_A2
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_FRAME_A2 uint8_t frame_a2_map[] = {
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0xff, 0x00, 0x00, 0xff, /* color #1 */
  0x40,
};
const lv_img_dsc_t frame_a2 = {
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
  .data = frame_a2_map,
};


#ifndef LV_ATTRIBUTE_IMG_FRAME_A3
#define LV_ATTRIBUTE_IMG_FRAME_A3
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_FRAME_A3 uint8_t frame_a3_map[] = {
  0x00, 0x00, 0x00, 0xff, /* color #0 */
  0xff, 0x00, 0x00, 0xff, /* color #1 */
  0x60,
};
const lv_img_dsc_t frame_a3 = {
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
  .data = frame_a3_map,
};


#ifndef LV_ATTRIBUTE_IMG_FRAME_B0
#define LV_ATTRIBUTE_IMG_FRAME_B0
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_FRAME_B0 uint8_t frame_b0_map[] = {
  0x00, 0x00, 0xff, 0xff, /* color #0 */
  0x00, 0xff, 0x00, 0xff, /* color #1 */
  0xff, 0x00, 0x00, 0xff, /* color #2 */
  0x00, 0x00, 0xff, 0xff, /* color #0 */
  0x90,
};
const lv_img_dsc_t frame_b0 = {
#if LVGL_VERSION_MAJOR >= 9
  .header.cf = LV_COLOR_FORMAT_I2,
#else
  .header.cf = LV_IMG_CF_INDEXED_2BIT,
  .header.always_zero = 0,
  .header.reserved = 0,
#endif
  .header.w = 3,
  .header.h = 1,
  .data_size = 17,
  .data = frame_b0_map,
};


#ifndef LV_ATTRIBUTE_IMG_FRAME_B1
#define LV_ATTRIBUTE_IMG_FRAME_B1
#endif
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_FRAME_B1 uint8_t frame_b1_map[] = {
  0x00, 0x00, 0xff, 0xff, /* color #0 */
  0x00, 0xff, 0x00, 0xff, /* color #1 */
  0xff, 0x00, 0x00, 0xff, /* color #2 */
  0x00, 0x00, 0xff, 0xff, /* color #0 */
  0x48,
};
const lv_img_dsc_t frame_b1 = {
#if LVGL_VERSION_MAJOR >= 9
  .header.cf = LV_COLOR_FORMAT_I2,
#else
  .header.cf = LV_IMG_CF_INDEXED_2BIT,
  .header.always_zero = 0,
  .header.reserved = 0,
#endif
  .header.w = 3,
  .header.h = 1,
  .data_size = 17,
  .data = frame_b1_map,
};


#ifndef _IMG_DSC_SEQ_STRUCT_
#define _IMG_DSC_SEQ_STRUCT_
struct img_dsc_seq {
const unsigned int count;
const lv_img_dsc_t *imgs[];
};
#endif  // _IMG_DSC_SEQ_STRUCT_

const struct img_dsc_seq frames_a = {3, {
  &frame_a1,
  &frame_a2,
  &frame_a3,
}};
const struct img_dsc_seq frames_b = {2, {
  &frame_b0,
  &frame_b1,
}};
