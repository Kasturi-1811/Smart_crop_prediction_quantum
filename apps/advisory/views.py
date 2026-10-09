
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import requests
import os
from google import genai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from PIL import Image, UnidentifiedImageError

@login_required

@login_required
def weather_advisory(request):
    import requests
    from django.shortcuts import render

    context = {
        "location": "",
        "weather": None,
        "error": None,
    }

    if request.method == "GET":
        location = request.GET.get("location", "").strip()
        latitude = request.GET.get("latitude", "").strip()
        longitude = request.GET.get("longitude", "").strip()

        try:
            if latitude and longitude:
                lat, lon = float(latitude), float(longitude)

                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Invalid GPS coordinates.")

                location = f"GPS location ({lat:.4f}, {lon:.4f})"

            elif location:
                geo = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": location,
                        "count": 10,
                        "language": "en",
                        "format": "json",
                    },
                    timeout=10,
                )
                geo.raise_for_status()
                places = geo.json().get("results", [])
                places = [
                    p for p in places if p.get("country_code") == "IN"
                ] or places

                if not places:
                    raise ValueError(
                        "Location not found. Enter a village or district."
                    )

                place = places[0]
                lat, lon = place["latitude"], place["longitude"]
                location = ", ".join(
                    str(x) for x in [
                        place.get("name"),
                        place.get("admin1"),
                        place.get("country"),
                    ] if x
                )
            else:
                return render(request, "advisory/weather.html", context)

            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "apparent_temperature,is_day,precipitation,rain,"
                        "weather_code,cloud_cover,wind_speed_10m,"
                        "wind_direction_10m"
                    ),
                    "daily": (
                        "weather_code,temperature_2m_max,temperature_2m_min,"
                        "precipitation_probability_max,precipitation_sum,"
                        "sunrise,sunset,sunshine_duration"
                    ),
                    "forecast_days": 3,
                    "timezone": "auto",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            current = data["current"]
            daily = data["daily"]

            descriptions = {
                0: ("Sunny / clear", "☀️"),
                1: ("Mostly clear", "🌤️"),
                2: ("Partly cloudy", "⛅"),
                3: ("Cloudy", "☁️"),
                45: ("Foggy", "🌫️"),
                48: ("Foggy", "🌫️"),
                51: ("Light drizzle", "🌦️"),
                53: ("Drizzle", "🌦️"),
                55: ("Heavy drizzle", "🌧️"),
                61: ("Light rain", "🌧️"),
                63: ("Moderate rain", "🌧️"),
                65: ("Heavy rain", "🌧️"),
                80: ("Rain showers", "🌦️"),
                81: ("Rain showers", "🌧️"),
                82: ("Heavy rain showers", "⛈️"),
                95: ("Thunderstorm", "⛈️"),
                96: ("Thunderstorm with hail", "⛈️"),
                99: ("Thunderstorm with hail", "⛈️"),
            }

            code = current.get("weather_code")
            description, icon = descriptions.get(
                code, ("Conditions unavailable", "🌡️")
            )

            days = []
            for i, date in enumerate(daily.get("time", [])):
                day_code = daily["weather_code"][i]
                day_description, day_icon = descriptions.get(
                    day_code, ("Conditions unavailable", "🌡️")
                )
                rain_chance = daily["precipitation_probability_max"][i]
                rain_total = daily["precipitation_sum"][i]

                days.append({
                    "date": date,
                    "description": day_description,
                    "icon": day_icon,
                    "max_temp": daily["temperature_2m_max"][i],
                    "min_temp": daily["temperature_2m_min"][i],
                    "rain_chance": rain_chance,
                    "rain_total": rain_total,
                    "sunrise": daily["sunrise"][i],
                    "sunset": daily["sunset"][i],
                    "sunshine_hours": round(
                        daily["sunshine_duration"][i] / 3600, 1
                    ),
                })

            # Basic weather-only guidance, not a crop-specific guarantee.
            today = days[0] if days else {}
            rain_chance = today.get("rain_chance")
            rain_total = today.get("rain_total", 0) or 0
            temperature = current.get("temperature_2m")
            wind = current.get("wind_speed_10m")
            weather_code = current.get("weather_code")

            if weather_code in (95, 96, 99) or (
                rain_chance is not None and rain_chance >= 70
            ):
                planting_status = "Wait and check"
                planting_reason = (
                    "Thunderstorms or a high chance of rain may disrupt "
                    "field work. Check local conditions before planting."
                )
            elif temperature is not None and temperature >= 38:
                planting_status = "Use caution"
                planting_reason = (
                    "High heat may stress seedlings. Consider cooler hours "
                    "and check the needs of your chosen crop."
                )
            elif wind is not None and wind >= 35:
                planting_status = "Use caution"
                planting_reason = (
                    "Strong winds may make field work difficult. "
                    "Check conditions before planting."
                )
            elif rain_chance is not None and rain_chance <= 30 and rain_total < 1:
                planting_status = "Check soil moisture"
                planting_reason = (
                    "Rain is unlikely today. Plant only if the crop, "
                    "soil moisture, and irrigation conditions are suitable."
                )
            else:
                planting_status = "Check crop and soil"
                planting_reason = (
                    "Weather alone cannot decide planting suitability. "
                    "Check crop requirements, soil moisture, and field conditions."
                )

            weather = {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "rain": current.get("rain"),
                "precipitation": current.get("precipitation"),
                "wind": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "cloud_cover": current.get("cloud_cover"),
                "description": description,
                "icon": icon,
                "is_day": current.get("is_day"),
                "updated_at": current.get("time"),
                "days": days,
                "planting_status": planting_status,
                "planting_reason": planting_reason,
            }

            context.update({"location": location, "weather": weather})

        except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
            context["error"] = (
                "Weather could not be loaded. Check your internet connection "
                "and try another village or district."
            )

    return render(request, "advisory/weather.html", context)



# Keep the other existing pages working
@login_required
def soil_analysis(request):
    result = None
    error = None
    selected_language = request.POST.get("language", "en")
    if selected_language not in ["en", "te", "hi"]:
        selected_language = "en"
    if request.method == "POST":
        uploaded_image = request.FILES.get("soil_image")

        if not uploaded_image:
            error = "Please take or upload a soil photo."
        elif uploaded_image.size > 5 * 1024 * 1024:
            error = "Please upload an image smaller than 5 MB."
        elif uploaded_image.content_type not in [
            "image/jpeg", "image/png", "image/webp"
        ]:
            error = "Please upload a JPG, PNG, or WebP image."
        else:
            try:
                image = Image.open(uploaded_image)
                image.verify()

                uploaded_image.seek(0)
                image = Image.open(uploaded_image).convert("RGB")

                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "Gemini API key is not configured on the server."
                    )

                from google.genai import types

                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(
                            attempts=4,
                            initial_delay=2,
                            max_delay=10,
                            exp_base=2,
                            http_status_codes=[503, 504],
                        )
                    ),
                )

                language_names = {
                    "en": "English",
                    "te": "Telugu",
                    "hi": "Hindi",
                }

                prompt = f"""
                Analyze this agricultural soil photograph for a farmer.

                IMPORTANT: Write the entire analysis in {language_names[selected_language]}.
                Use simple, natural language that farmers can understand.

                Include these four sections:
                1. Visible soil color and texture
                2. What the visible characteristics may mean
                3. What cannot be determined from a photo, including pH and NPK
                4. Practical next steps for assessing the soil

                Use short paragraphs and simple bullet points.
                Do not use Markdown formatting symbols.
                Do not invent nutrient measurements or guarantee crop suitability.
                Recommend laboratory testing when appropriate.
                If the image is not a soil photo, explain that clearly.
                """

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[prompt, image],
                )

                result = response.text or (
                    "The AI did not return an analysis. Please try again."
                )

            except (UnidentifiedImageError, OSError):
                error = "This image could not be opened. Please try another."
            except ValueError as exc:
                error = str(exc)
            except Exception as exc:
                print("GEMINI SOIL PHOTO ERROR:", repr(exc))
                error = (
                    "Soil photo analysis failed. Please check the Django terminal "
                    "for the exact error."
                )

    return render(
        request,
        "advisory/soil_photo_analysis.html",
        {
            "result": result,
            "error": error,
            "selected_language": selected_language,
        },
    )
    


@login_required
def crop_recommendation(request):
    import requests
    from django.shortcuts import render

    context = {
        "recommendations": [],
        "error": None,
        "submitted": False,
    }

    # Starter crop profiles for a general Indian farming demo.
    # Verify these against local agricultural guidance before real use.
    crops = [
        {
            "name": "Rice",
            "seasons": ["kharif", "rabi"],
            "min_temp": 20, "max_temp": 35,
            "water": "high",
            "soils": ["clay", "loam"],
            "note": "Often needs reliable water and suitable field conditions.",
        },
        {
            "name": "Maize",
            "seasons": ["kharif", "rabi", "summer"],
            "min_temp": 18, "max_temp": 35,
            "water": "medium",
            "soils": ["loam", "sandy"],
            "note": "Needs suitable moisture, drainage, and seasonal temperatures.",
        },
        {
            "name": "Groundnut",
            "seasons": ["kharif", "summer"],
            "min_temp": 20, "max_temp": 35,
            "water": "medium",
            "soils": ["sandy", "loam"],
            "note": "Well-drained soil is generally important.",
        },
        {
            "name": "Red gram (Pigeon pea)",
            "seasons": ["kharif"],
            "min_temp": 20, "max_temp": 35,
            "water": "low",
            "soils": ["sandy", "loam"],
            "note": "Can tolerate some dry conditions once established.",
        },
        {
            "name": "Green gram",
            "seasons": ["kharif", "summer"],
            "min_temp": 20, "max_temp": 35,
            "water": "low",
            "soils": ["sandy", "loam"],
            "note": "Usually suited to warm conditions and well-drained soil.",
        },
        {
            "name": "Chickpea",
            "seasons": ["rabi"],
            "min_temp": 10, "max_temp": 30,
            "water": "low",
            "soils": ["sandy", "loam"],
            "note": "Generally a cool-season crop; avoid waterlogging.",
        },
        {
            "name": "Sorghum (Jowar)",
            "seasons": ["kharif", "rabi", "summer"],
            "min_temp": 20, "max_temp": 35,
            "water": "low",
            "soils": ["sandy", "loam", "clay"],
            "note": "Relatively drought-tolerant, depending on variety and stage.",
        },
        {
            "name": "Pearl millet (Bajra)",
            "seasons": ["kharif", "summer"],
            "min_temp": 22, "max_temp": 38,
            "water": "low",
            "soils": ["sandy", "loam"],
            "note": "Heat- and drought-tolerant compared with many crops.",
        },
    ]

    if request.method == "POST":
        context["submitted"] = True

        location = request.POST.get("location", "").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()
        season = request.POST.get("season", "").lower()
        water = request.POST.get("water", "").lower()
        soil = request.POST.get("soil_type", "").lower()

        context["form_data"] = {
            "location": location,
            "season": season,
            "water": water,
            "soil_type": soil,
        }

        try:
            # Resolve coordinates from GPS or a manually entered place.
            if latitude and longitude:
                lat, lon = float(latitude), float(longitude)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Invalid GPS coordinates.")
                location_label = f"GPS ({lat:.3f}, {lon:.3f})"

            elif location:
                geo = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": location,
                        "count": 10,
                        "language": "en",
                        "format": "json",
                    },
                    timeout=10,
                )
                geo.raise_for_status()
                places = geo.json().get("results", [])
                indian_places = [
                    p for p in places if p.get("country_code") == "IN"
                ]
                places = indian_places or places

                if not places:
                    raise ValueError("Location not found. Try a nearby town or district.")

                place = places[0]
                lat, lon = place["latitude"], place["longitude"]
                location_label = ", ".join(
                    str(x) for x in [
                        place.get("name"), place.get("admin1"), place.get("country")
                    ] if x
                )
            else:
                raise ValueError("Enter your village/district or use GPS.")

            if season not in ["kharif", "rabi", "summer"]:
                raise ValueError("Please select a season.")
            if water not in ["low", "medium", "high"]:
                raise ValueError("Please select water availability.")

            # Get current temperature and 3-day forecast.
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m",
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,"
                        "precipitation_probability_max,precipitation_sum"
                    ),
                    "forecast_days": 3,
                    "timezone": "auto",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            current_temp = data["current"]["temperature_2m"]
            daily = data["daily"]

            rain_chances = [
                value for value in daily.get("precipitation_probability_max", [])
                if value is not None
            ]
            rain_totals = [
                value for value in daily.get("precipitation_sum", [])
                if value is not None
            ]
            avg_rain_chance = (
                sum(rain_chances) / len(rain_chances) if rain_chances else None
            )
            forecast_rain_mm = sum(rain_totals) if rain_totals else 0

            results = []

            for crop in crops:
                score = 0
                reasons = []

                if season in crop["seasons"]:
                    score += 35
                    reasons.append("season matches the crop profile")
                else:
                    score -= 25
                    reasons.append("season may not be suitable")

                if crop["min_temp"] <= current_temp <= crop["max_temp"]:
                    score += 25
                    reasons.append("current temperature is within its broad range")
                else:
                    score -= 10
                    reasons.append("current temperature is outside its broad range")

                water_rank = {"low": 1, "medium": 2, "high": 3}
                crop_water_rank = water_rank[crop["water"]]
                farmer_water_rank = water_rank[water]

                if farmer_water_rank >= crop_water_rank:
                    score += 20
                    reasons.append("water availability may meet its broad needs")
                else:
                    score -= 20
                    reasons.append("available water may be insufficient")

                if soil and soil in crop["soils"]:
                    score += 15
                    reasons.append("selected soil type matches the crop profile")
                elif soil:
                    score -= 5
                    reasons.append("selected soil type is not a preferred match")
                else:
                    reasons.append("soil type was not provided")

                # Small adjustment from forecast; not a full rainfall model.
                if avg_rain_chance is not None:
                    if avg_rain_chance >= 70 and crop["water"] == "high":
                        score += 5
                        reasons.append("forecast suggests a chance of rain")
                    elif avg_rain_chance <= 20 and crop["water"] == "high":
                        score -= 5
                        reasons.append("little rain is forecast; irrigation may be needed")

                results.append({
                    "name": crop["name"],
                    "score": max(0, min(100, score)),
                    "reasons": reasons,
                    "note": crop["note"],
                })

            results.sort(key=lambda item: item["score"], reverse=True)

            context.update({
                "recommendations": results[:5],
                "location_label": location_label,
                "temperature": current_temp,
                "forecast_rain_mm": round(forecast_rain_mm, 1),
                "rain_chance": (
                    round(avg_rain_chance) if avg_rain_chance is not None else None
                ),
            })

        except (requests.RequestException, ValueError, KeyError, TypeError):
            context["error"] = (
                "We couldn't generate recommendations. Check your location, "
                "selected options, and internet connection, then try again."
            )

    return render(request, "advisory/crop_recommendation.html", context)




@login_required
def disease_detection(request):
    result = None
    error = None
    selected_language = request.POST.get("language", "en")
    crop_name = request.POST.get("crop_name", "").strip()

    if selected_language not in ["en", "te", "hi"]:
        selected_language = "en"

    if request.method == "POST":
        uploaded_image = request.FILES.get("crop_image")

        if not uploaded_image:
            error = "Please take or upload a crop photo."
        elif uploaded_image.size > 5 * 1024 * 1024:
            error = "Please upload an image smaller than 5 MB."
        elif uploaded_image.content_type not in [
            "image/jpeg", "image/png", "image/webp"
        ]:
            error = "Please upload a JPG, PNG, or WebP image."
        else:
            try:
                image = Image.open(uploaded_image)
                image.verify()

                uploaded_image.seek(0)
                image = Image.open(uploaded_image).convert("RGB")

                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "Gemini API key is not configured on the server."
                    )

                from google.genai import types

                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(
                            attempts=4,
                            initial_delay=2,
                            max_delay=10,
                            exp_base=2,
                            http_status_codes=[503, 504],
                        )
                    ),
                )

                language_names = {
                    "en": "English",
                    "te": "Telugu",
                    "hi": "Hindi",
                }

                crop_context = (
                    f"The farmer identifies the crop as: {crop_name}."
                    if crop_name
                    else "The crop species has not been provided."
                )

                prompt = f"""
                You are an agricultural crop-health assistant.

                Write your complete response in {language_names[selected_language]}.
                Use simple language that farmers can understand.

                Crop information: {crop_context}

                Examine the uploaded image and provide these sections:

                1. IMAGE OBSERVATIONS
                Describe visible leaf color, spots, holes, wilting,
                discoloration, or other observable symptoms.

                2. POSSIBLE CAUSES
                Explain possible disease, pest damage, nutrient stress,
                environmental stress, or other causes only when supported
                by visible evidence. Distinguish possibilities from facts.

                3. WHAT TO CHECK NEXT
                Suggest practical observations the farmer can make,
                such as inspecting both sides of leaves and nearby plants.

                4. RECOMMENDED NEXT STEPS
                Give cautious, practical guidance. Recommend local
                agricultural expert advice if symptoms are serious or unclear.

                5. LIMITATIONS
                Explain that a photograph cannot always confirm a disease.
                Do not invent laboratory results or claim certainty.
                Do not prescribe a specific pesticide or dosage without
                adequate diagnosis and reliable crop-specific guidance.

                If the image is not a crop or plant image, say that clearly.
                If the image is unclear, ask for a clearer photo.
                Do not claim to detect a disease when evidence is insufficient.
                Use short paragraphs and simple bullet points.
                """

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[prompt, image],
                )

                result = response.text or (
                    "No analysis was returned. Please try again."
                )

            except (UnidentifiedImageError, OSError):
                error = "This image could not be opened. Please upload another."
            except ValueError as exc:
                error = str(exc)
            except Exception as exc:
                print("GEMINI CROP HEALTH ERROR:", repr(exc))
                error = (
                    "Crop health analysis is temporarily unavailable. "
                    "Please try again later."
                )

    return render(
        request,
        "advisory/disease_detection.html",
        {
            "result": result,
            "error": error,
            "selected_language": selected_language,
            "crop_name": crop_name,
        },
    )


@login_required
def farm_economics(request):
    return render(request, "farms/economics.html")

@login_required
def soil_photo_analysis(request):
    result = None
    error = None
    selected_language = request.POST.get("language", "en")
    if selected_language not in ["en", "te", "hi"]:
        selected_language = "en"
    if request.method == "POST":
        uploaded_image = request.FILES.get("soil_image")

        if not uploaded_image:
            error = "Please take or upload a soil photo."
        elif uploaded_image.size > 5 * 1024 * 1024:
            error = "Please upload an image smaller than 5 MB."
        elif uploaded_image.content_type not in [
            "image/jpeg", "image/png", "image/webp"
        ]:
            error = "Please upload a JPG, PNG, or WebP image."
        else:
            try:
                image = Image.open(uploaded_image)
                image.verify()

                uploaded_image.seek(0)
                image = Image.open(uploaded_image).convert("RGB")

                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "Gemini API key is not configured on the server."
                    )

                from google.genai import types

                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(
                            attempts=4,
                            initial_delay=2,
                            max_delay=10,
                            exp_base=2,
                            http_status_codes=[503, 504],
                        )
                    ),
                )
                language_names = {
                    "en": "English",
                    "te": "Telugu",
                    "hi": "Hindi",
                }

                prompt = f"""
                Analyze this agricultural soil photograph for a farmer.

                IMPORTANT: Write the entire analysis in {language_names[selected_language]}.
                Use simple, natural language that farmers can understand.

                Include these four sections:
                1. Visible soil color and texture
                2. What the visible characteristics may mean
                3. What cannot be determined from a photo, including pH and NPK
                4. Practical next steps for assessing the soil

                Use short paragraphs and simple bullet points.
                Do not use Markdown formatting symbols.
                Do not invent nutrient measurements or guarantee crop suitability.
                Recommend laboratory testing when appropriate.
                If the image is not a soil photo, explain that clearly.
                """
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=[prompt, image],
                )

                result = response.text or (
                    "The AI did not return an analysis. Please try again."
                )

            except (UnidentifiedImageError, OSError):
                error = "This image could not be opened. Please try another."
            except ValueError as exc:
                error = str(exc)
            except Exception as exc:
                print("GEMINI SOIL PHOTO ERROR:", repr(exc))
                error = (
                    "Soil photo analysis failed. Please check the Django terminal "
                    "for the exact error."
                )

    return render(
        request,
        "advisory/soil_photo_analysis.html",
        {
            "result": result,
            "error": error,
            "selected_language": selected_language,
        },
    )