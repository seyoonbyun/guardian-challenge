// +1 Challenge 2026 - Google Apps Script
// Sheet tab: "2026" (auto-create if not exists)
// Form: invite.html -> action=addData
// Dashboard: challenge-dashboard.html -> action=getData (returns array)
// Awards: challenge.html -> action=getData (returns array)

// ===== Sheet Helper =====
function getOrCreateSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("2026");
  if (!sheet) {
    sheet = ss.insertSheet("2026");
    var headers = ["등록일시","영입멤버명","지역명","챕터명","연락처","신규멤버성함","신규멤버연락처","입회챕터","가입여부","90G2F유형","점수","중복체크키"];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#4285f4").setFontColor("#ffffff");
    sheet.setFrozenRows(1);
  }
  return sheet;
}

// ===== Main Router =====
function doGet(e) {
  try {
    var action = (e.parameter.action || "").trim();

    if (action === "addData") {
      return addData(e);
    } else if (action === "getData") {
      return getData();
    } else if (action === "debugSheet") {
      return debugSheet();
    } else {
      return jsonResponse({
        success: false,
        error: "INVALID_ACTION",
        message: "Supported actions: addData, getData, debugSheet"
      });
    }
  } catch (error) {
    console.error("doGet error:", error);
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// ===== Save Data (invite.html form) =====
function addData(e) {
  try {
    var p = e.parameter;

    // Required fields
    var referrerName = (p.referrerName || "").trim();
    var referrerRegion = (p.referrerRegion || "").trim();
    var referrerChapter = (p.referrerChapter || "").trim();
    var referrerContact = (p.referrerContact || "").trim();
    var newMemberName = (p.newMemberName || "").trim();
    var newMemberContact = (p.newMemberContact || "").trim();
    var newMemberChapter = (p.newMemberChapter || "").trim();

    if (!referrerName || !referrerRegion || !referrerChapter || !referrerContact ||
        !newMemberName || !newMemberContact || !newMemberChapter) {
      return jsonResponse({
        success: false,
        error: "MISSING_REQUIRED_FIELDS",
        message: "Required fields are missing."
      });
    }

    // Name min length
    if (referrerName.length < 2 || newMemberName.length < 2) {
      return jsonResponse({
        success: false,
        error: "INVALID_NAME_LENGTH",
        message: "Name must be at least 2 characters."
      });
    }

    var sheet = getOrCreateSheet();

    // Duplicate check by uniqueKey
    var uniqueKey = (p.uniqueKey || "").trim();
    if (uniqueKey) {
      var existingData = sheet.getDataRange().getValues();
      for (var i = 1; i < existingData.length; i++) {
        if ((existingData[i][11] || "").toString().trim() === uniqueKey) {
          return jsonResponse({
            success: false,
            error: "DUPLICATE_DATA",
            message: "Already registered."
          });
        }
      }
    }

    // Parse values
    var g2fType = (p.g2fType || "").trim();
    var joinedMember = (p.joinedMember === "true");
    var score = parseInt(p.score) || 0;

    // createdAt from form (KST), fallback to server time
    var createdAt = (p.createdAt || "").trim();
    if (!createdAt) {
      createdAt = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy. MM. dd. HH:mm:ss");
    }

    // Append row (columns A~L)
    sheet.appendRow([
      createdAt,
      referrerName,
      referrerRegion,
      referrerChapter,
      referrerContact,
      newMemberName,
      newMemberContact,
      newMemberChapter,
      joinedMember,
      g2fType,
      score,
      uniqueKey
    ]);

    return jsonResponse({
      success: true,
      message: "Data saved successfully.",
      score: score,
      is90G2FQualified: (g2fType !== "")
    });

  } catch (error) {
    console.error("addData error:", error);
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// ===== Get Data (Dashboard + Awards shared) =====
// Dashboard expects a plain array
// Awards uses: data.data || data
function getData() {
  try {
    var sheet = getOrCreateSheet();
    var data = sheet.getDataRange().getValues();

    if (data.length <= 1) {
      return jsonResponse([]);
    }

    var headers = data[0];
    var rows = data.slice(1);
    var result = [];

    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];

      // Skip empty rows
      var name = (row[1] || "").toString().trim();
      if (!name) continue;

      var g2fType = (row[9] || "").toString().trim();

      result.push({
        timestamp: row[0] || "",
        createdAt: row[0] || "",
        referrerName: row[1] || "",
        myName: row[1] || "",
        referrerRegion: row[2] || "",
        myRegion: row[2] || "",
        referrerChapter: row[3] || "",
        myChapter: row[3] || "",
        referrerContact: row[4] || "",
        myContact: row[4] || "",
        newMemberName: row[5] || "",
        newMemberContact: row[6] || "",
        newMemberChapter: row[7] || "",
        joinedMember: row[8] || false,
        g2fType: g2fType,
        memberType: g2fType,
        is90G2FQualified: g2fType !== "",
        score: row[10] || 0,
        uniqueKey: row[11] || ""
      });
    }

    return jsonResponse(result);

  } catch (error) {
    console.error("getData error:", error);
    return jsonResponse({ success: false, error: error.toString() });
  }
}


// ===== Debug Sheet =====
function debugSheet() {
  try {
    var sheet = getOrCreateSheet();
    var data = sheet.getDataRange().getValues();

    return jsonResponse({
      success: true,
      sheetName: sheet.getName(),
      totalRows: data.length,
      headers: data.length > 0 ? data[0] : [],
      sampleData: data.slice(0, Math.min(4, data.length)),
      lastUpdate: new Date().toISOString()
    });
  } catch (error) {
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// ===== JSON Response Helper =====
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
