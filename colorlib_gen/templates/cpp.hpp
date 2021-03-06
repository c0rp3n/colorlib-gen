//
// This file was generated with color_gen.py
//
// Do not edit! Regenerate this file with color_gen.py (see https://github.com/c0rp3n/colorlib-gen)
//

#ifndef _{{ file_name|upper }}_HPP_
#define _{{ file_name|upper }}_HPP_

#pragma once

#include <utility>

#ifdef COLORLIB_USE_INLINE
#define CL_INLINE inline
#else
#define CL_INLINE
#endif

#ifdef COLORLIB_USE_CONSTEXPR
#define CL_CONSTEXPR constexpr
#else
#define CL_CONSTEXPR
#endif

enum struct {{ enum_name }} : char
{
{%- for (enum, value) in colors %}
    {{ enum }} = {{ value }},
{%- endfor %}
};

CL_CONSTEXPR CL_INLINE std::tuple<{{ enum_name }}, int> {{ function_name }}(const char* color)
{
{%- for (depth, key, length, value) in decisions recursive %}
    {%- if loop.index == 1 %}
    if (color[{{ depth }}] == {% if key is string -%} '{{ key }}' {%- else -%} {{ key }} {%- endif %})
    {
        {%- if value is not string -%}
        {{ loop(value)|indent(4) }}
        {%- else %}
        return std::make_tuple({{ enum_name }}::{{ value }}, {{ length }});
        {%- endif %}
    }
    {%- else %}
    else if (color[{{ depth }}] == {% if key is string -%} '{{ key }}' {%- else -%} {{ key }} {%- endif %})
    {
        {%- if value is not string -%}
        {{ loop(value)|indent(4) }}
        {%- else %}
        return std::make_tuple({{ enum_name }}::{{ value }}, {{ length }});
        {%- endif %}
    }
    {%- endif %}
{%- endfor %}

    return std::make_tuple(static_cast<{{ enum_name }}>(0x00), 0);
}

#undef CL_INLINE
#undef CL_CONSTEXPR

#endif // _{{ file_name|upper }}_HPP_
