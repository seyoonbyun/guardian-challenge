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
    var headers = ["createdAt","referrerName","referrerRegion","referrerChapter","referrerContact","newMemberName","newMemberContact","newMemberChapter","joinedMember","is90Born","isGlobal","isSecondGenOwner","isFranchise","is90G2FQualified","score","uniqueKey"];
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
        if ((existingData[i][15] || "").toString().trim() === uniqueKey) {
          return jsonResponse({
            success: false,
            error: "DUPLICATE_DATA",
            message: "Already registered."
          });
        }
      }
    }

    // Parse checkbox values
    var is90Born = (p.is90Born === "true");
    var isGlobal = (p.isGlobal === "true");
    var isSecondGenOwner = (p.isSecondGenOwner === "true");
    var isFranchise = (p.isFranchise === "true");
    var is90G2FQualified = (p.is90G2FQualified === "true");
    var joinedMember = (p.joinedMember === "true");
    var score = parseInt(p.score) || 0;

    // createdAt from form (KST), fallback to server time
    var createdAt = (p.createdAt || "").trim();
    if (!createdAt) {
      createdAt = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy. MM. dd. HH:mm:ss");
    }

    // Append row (columns A~P)
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
      is90Born,
      isGlobal,
      isSecondGenOwner,
      isFranchise,
      is90G2FQualified,
      score,
      uniqueKey
    ]);

    return jsonResponse({
      success: true,
      message: "Data saved successfully.",
      score: score,
      is90G2FQualified: is90G2FQualified
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

      result.push({
        // Dashboard fields (challenge-dashboard.html)
        timestamp: row[0] || "",
        myRegion: row[2] || "",
        myChapter: row[3] || "",
        myName: row[1] || "",
        myContact: row[4] || "",
        newMemberName: row[5] || "",
        newMemberChapter: row[7] || "",
        memberType: getMemberType(row),

        // Awards fields (challenge.html)
        createdAt: row[0] || "",
        referrerName: row[1] || "",
        referrerRegion: row[2] || "",
        referrerChapter: row[3] || "",
        referrerContact: row[4] || "",
        newMemberContact: row[6] || "",

        // New fields
        joinedMember: row[8] || false,
        is90Born: row[9] || false,
        isGlobal: row[10] || false,
        isSecondGenOwner: row[11] || false,
        isFranchise: row[12] || false,
        is90G2FQualified: row[13] || false,
        score: row[14] || 0,
        uniqueKey: row[15] || ""
      });
    }

    return jsonResponse(result);

  } catch (error) {
    console.error("getData error:", error);
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// Member type string for legacy dashboard compatibility
function getMemberType(row) {
  var types = [];
  if (row[9] === true || row[9] === "true") types.push("90born");
  if (row[10] === true || row[10] === "true") types.push("global");
  if (row[11] === true || row[11] === "true") types.push("2ndGen");
  if (row[12] === true || row[12] === "true") types.push("franchise");
  return types.join(", ") || "";
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
