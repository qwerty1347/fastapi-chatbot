openapis = [
    (
        "getItemList, 상품리스트, 상품 목록 조회",
        "종류: Open API",
        "요청 URL: https://domeggook.com/ssl/api/",
        "요청 방식: GET",
        "API명: 상품리스트",
        "버전: 1.0, 4.0, 4.1",
        "모드: getItemList",
        "API 설명: 주어진 조건에 해당하는 상품들의 목록을 반환하는 API입니다, 본 API를 통해 수신한 상품목록은 도매꾹·도매매 웹서비스의 상품목록과 동일합니다, 판매중인 상품 정보만 반환하며, 판매중지·종료·품단종 상품은 제외됩니다",
        "필수 파라미터: ver, mode, aid, market, so, ev, ca, kw",
        "선택 파라미터: sz, pg, ca, id, nick, swi, swe, mnp, mxp, mnq, mxq, who, org, sgd, fdl, useopt, shp, lwp, cnew, com, periodEntrySeller, periodEntryItem, usePriceComparison, dfos, identify[id], identify[ip], identify[sess], allitem, ext",
    ),
    (
        "getItemView, 상품상세정보, 상품 상세정보 조회",
        "종류: Open API",
        "요청 URL: https://domeggook.com/ssl/api/",
        "요청 방식: GET",
        "API명: 상품상세정보",
        "버전: 1.0, 4.0 4.1, 4.2, 4.3, 4.4, 4.5",
        "모드: getItemView",
        "API 설명: 어떤 상품 1개에 대한 상세한 정보를 조회할 수 있는 API입니다.",
        "필수 파라미터: ver, mode, aid, no, om",
        "선택 파라미터: multiple, allItem, sellerId, sId, ext, mailzine, market, admin"
    ),
    (
        "getImageAllowItems, 이미지허용상품정보, 이미지 허용 상품정보 조회",
        "종류: Open API",
        "요청 URL: https://domeggook.com/ssl/api/",
        "요청 방식: POST",
        "버전: 1.0, 1.1",
        "모드: getImageAllowItems",
        "API 설명: 도매꾹 상품 중 진열/판매중이며, 이미지사용허용인 상품들을 리턴하는 api 입니다, 1 페이지당 20개의 상품의 정보를 리턴합니다 (연길법인만 사용가능)"
    )
]