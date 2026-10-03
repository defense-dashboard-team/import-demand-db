"""plotly 차트 클릭(선택) 이벤트 읽기."""


def extract_selected_point(event):
    try:
        points = event.selection.points
    except Exception:
        try:
            points = event["selection"]["points"]
        except Exception:
            return None

    if not points:
        return None

    return points[-1]
