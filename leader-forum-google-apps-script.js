/**
 * 리더 포럼 출석 관리 시스템 - 구글 앱스 스크립트
 * 구글 시트와 웹 페이지를 실시간으로 연동하는 백엔드 코드
 */

// 구글 시트 설정
const SHEET_ID = 'YOUR_GOOGLE_SHEET_ID'; // 실제 구글 시트 ID로 변경 필요
const SHEET_NAMES = {
  USERS: 'Users',           // 유저 정보
  SESSIONS: 'Sessions',      // 포럼 세션 정보
  ATTENDANCE: 'Attendance', // 출석 기록
  MANAGERS: 'Managers',     // 포럼 책임자 정보
  LINKS: 'Links'           // 포럼 링크 정보
};

// 포럼 클래스 목록
const FORUM_CLASSES = [
  '내셔널 트레이너 포럼',
  'PR 코디 포럼',
  '도어퍼슨 포럼',
  '비지터 호스트 포럼',
  '성장 코디 포럼',
  '멤버십 위원회 포럼',
  '교육 코디네이터 포럼',
  '멘토링 코디 포럼',
  '의장단 포럼'
];

/**
 * 웹 앱 진입점 - GET 요청 처리
 */
function doGet(e) {
  const action = e.parameter.action || 'getData';
  
  try {
    switch (action) {
      case 'getData':
        return getSystemData();
      case 'login':
        return handleLogin(e.parameter);
      case 'getUserData':
        return getUserData(e.parameter);
      case 'updateAttendance':
        return updateAttendance(e.parameter);
      case 'getSessions':
        return getSessions(e.parameter);
      case 'getUsers':
        return getUsers(e.parameter);
      default:
        return createResponse({ error: 'Invalid action' }, 400);
    }
  } catch (error) {
    console.error('Error in doGet:', error);
    return createResponse({ error: error.message }, 500);
  }
}

/**
 * 웹 앱 진입점 - POST 요청 처리
 */
function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  const action = data.action;
  
  try {
    switch (action) {
      case 'createUser':
        return createUser(data);
      case 'createSession':
        return createSession(data);
      case 'updateSession':
        return updateSession(data);
      case 'deleteSession':
        return deleteSession(data);
      case 'createManager':
        return createManager(data);
      case 'updateManager':
        return updateManager(data);
      case 'createLink':
        return createLink(data);
      case 'updateLink':
        return updateLink(data);
      default:
        return createResponse({ error: 'Invalid action' }, 400);
    }
  } catch (error) {
    console.error('Error in doPost:', error);
    return createResponse({ error: error.message }, 500);
  }
}

/**
 * 시스템 전체 데이터 조회
 */
function getSystemData() {
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  
  const usersData = getSheetData(spreadsheet, SHEET_NAMES.USERS);
  const sessionsData = getSheetData(spreadsheet, SHEET_NAMES.SESSIONS);
  const attendanceData = getSheetData(spreadsheet, SHEET_NAMES.ATTENDANCE);
  const managersData = getSheetData(spreadsheet, SHEET_NAMES.MANAGERS);
  const linksData = getSheetData(spreadsheet, SHEET_NAMES.LINKS);
  
  return createResponse({
    users: usersData,
    sessions: sessionsData,
    attendance: attendanceData,
    managers: managersData,
    links: linksData,
    forumClasses: FORUM_CLASSES
  });
}

/**
 * 로그인 처리
 */
function handleLogin(params) {
  const { region, chapter, email, pin, className } = params;
  
  if (!region || !chapter || !email || !pin || !className) {
    return createResponse({ error: 'Missing required parameters' }, 400);
  }
  
  // 관리자 체크
  if (region === 'ADMIN' && chapter === 'ADMIN' && email === 'admin@leaderforum.com' && pin === '0000') {
    return createResponse({
      success: true,
      user: { role: 'admin', name: '관리자' }
    });
  }
  
  // 일반 사용자 체크
  const user = findUser(region, chapter, email, pin, className);
  if (user) {
    return createResponse({
      success: true,
      user: user
    });
  }
  
  return createResponse({ error: 'Invalid credentials' }, 401);
}

/**
 * 사용자 데이터 조회
 */
function getUserData(params) {
  const { userId } = params;
  
  if (!userId) {
    return createResponse({ error: 'User ID required' }, 400);
  }
  
  const user = getUserById(userId);
  if (!user) {
    return createResponse({ error: 'User not found' }, 404);
  }
  
  // 출석 기록 조회
  const attendance = getAttendanceByUserId(userId);
  
  return createResponse({
    user: user,
    attendance: attendance
  });
}

/**
 * 출석 업데이트
 */
function updateAttendance(params) {
  const { userId, sessionId, attended } = params;
  
  if (!userId || !sessionId || attended === undefined) {
    return createResponse({ error: 'Missing required parameters' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.ATTENDANCE);
  
  if (!sheet) {
    return createResponse({ error: 'Attendance sheet not found' }, 404);
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // 기존 출석 기록 찾기
  let rowIndex = -1;
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === userId && data[i][1] === sessionId) {
      rowIndex = i + 1;
      break;
    }
  }
  
  if (rowIndex === -1) {
    // 새 출석 기록 추가
    const newRow = [userId, sessionId, attended, new Date()];
    sheet.appendRow(newRow);
  } else {
    // 기존 출석 기록 업데이트
    sheet.getRange(rowIndex, 3).setValue(attended);
    sheet.getRange(rowIndex, 4).setValue(new Date());
  }
  
  return createResponse({ success: true });
}

/**
 * 세션 목록 조회
 */
function getSessions(params) {
  const { className } = params;
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.SESSIONS);
  
  if (!sheet) {
    return createResponse({ error: 'Sessions sheet not found' }, 404);
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const sessions = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const session = {};
    
    headers.forEach((header, index) => {
      session[header] = row[index];
    });
    
    if (!className || session.className === className) {
      sessions.push(session);
    }
  }
  
  return createResponse({ sessions: sessions });
}

/**
 * 사용자 목록 조회
 */
function getUsers(params) {
  const { className } = params;
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.USERS);
  
  if (!sheet) {
    return createResponse({ error: 'Users sheet not found' }, 404);
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const users = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const user = {};
    
    headers.forEach((header, index) => {
      user[header] = row[index];
    });
    
    if (!className || user.className === className) {
      users.push(user);
    }
  }
  
  return createResponse({ users: users });
}

/**
 * 새 사용자 생성
 */
function createUser(data) {
  const { region, chapter, email, pin, className, name } = data;
  
  if (!region || !chapter || !email || !pin || !className || !name) {
    return createResponse({ error: 'Missing required fields' }, 400);
  }
  
  // 중복 체크
  const existingUser = findUser(region, chapter, email, pin, className);
  if (existingUser) {
    return createResponse({ error: 'User already exists' }, 409);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.USERS);
  
  if (!sheet) {
    return createResponse({ error: 'Users sheet not found' }, 404);
  }
  
  const userId = generateUserId();
  const newUser = {
    id: userId,
    region: region,
    chapter: chapter,
    email: email,
    pin: pin,
    className: className,
    name: name,
    createdAt: new Date(),
    stamps: Array(12).fill(false) // 12개 스탬프 슬롯
  };
  
  const row = [
    newUser.id,
    newUser.region,
    newUser.chapter,
    newUser.email,
    newUser.pin,
    newUser.className,
    newUser.name,
    newUser.createdAt,
    JSON.stringify(newUser.stamps)
  ];
  
  sheet.appendRow(row);
  
  return createResponse({ success: true, user: newUser });
}

/**
 * 새 세션 생성
 */
function createSession(data) {
  const { title, date, time, type, location, onlineLink, className, managerId } = data;
  
  if (!title || !date || !time || !type || !className) {
    return createResponse({ error: 'Missing required fields' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.SESSIONS);
  
  if (!sheet) {
    return createResponse({ error: 'Sessions sheet not found' }, 404);
  }
  
  const sessionId = generateSessionId();
  const newSession = {
    id: sessionId,
    title: title,
    date: date,
    time: time,
    type: type,
    location: location || '',
    onlineLink: onlineLink || '',
    className: className,
    managerId: managerId || '',
    createdAt: new Date()
  };
  
  const row = [
    newSession.id,
    newSession.title,
    newSession.date,
    newSession.time,
    newSession.type,
    newSession.location,
    newSession.onlineLink,
    newSession.className,
    newSession.managerId,
    newSession.createdAt
  ];
  
  sheet.appendRow(row);
  
  return createResponse({ success: true, session: newSession });
}

/**
 * 세션 업데이트
 */
function updateSession(data) {
  const { sessionId, title, date, time, type, location, onlineLink, className, managerId } = data;
  
  if (!sessionId) {
    return createResponse({ error: 'Session ID required' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.SESSIONS);
  
  if (!sheet) {
    return createResponse({ error: 'Sessions sheet not found' }, 404);
  }
  
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === sessionId) {
      rowIndex = i + 1;
      break;
    }
  }
  
  if (rowIndex === -1) {
    return createResponse({ error: 'Session not found' }, 404);
  }
  
  // 업데이트할 필드들
  if (title !== undefined) sheet.getRange(rowIndex, 2).setValue(title);
  if (date !== undefined) sheet.getRange(rowIndex, 3).setValue(date);
  if (time !== undefined) sheet.getRange(rowIndex, 4).setValue(time);
  if (type !== undefined) sheet.getRange(rowIndex, 5).setValue(type);
  if (location !== undefined) sheet.getRange(rowIndex, 6).setValue(location);
  if (onlineLink !== undefined) sheet.getRange(rowIndex, 7).setValue(onlineLink);
  if (className !== undefined) sheet.getRange(rowIndex, 8).setValue(className);
  if (managerId !== undefined) sheet.getRange(rowIndex, 9).setValue(managerId);
  
  return createResponse({ success: true });
}

/**
 * 세션 삭제
 */
function deleteSession(data) {
  const { sessionId } = data;
  
  if (!sessionId) {
    return createResponse({ error: 'Session ID required' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.SESSIONS);
  
  if (!sheet) {
    return createResponse({ error: 'Sessions sheet not found' }, 404);
  }
  
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === sessionId) {
      rowIndex = i + 1;
      break;
    }
  }
  
  if (rowIndex === -1) {
    return createResponse({ error: 'Session not found' }, 404);
  }
  
  sheet.deleteRow(rowIndex);
  
  return createResponse({ success: true });
}

/**
 * 포럼 책임자 생성
 */
function createManager(data) {
  const { forumClass, name, email, phone, region, chapter } = data;
  
  if (!forumClass || !name || !email) {
    return createResponse({ error: 'Missing required fields' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.MANAGERS);
  
  if (!sheet) {
    return createResponse({ error: 'Managers sheet not found' }, 404);
  }
  
  const managerId = generateManagerId();
  const newManager = {
    id: managerId,
    forumClass: forumClass,
    name: name,
    email: email,
    phone: phone || '',
    region: region || '',
    chapter: chapter || '',
    createdAt: new Date()
  };
  
  const row = [
    newManager.id,
    newManager.forumClass,
    newManager.name,
    newManager.email,
    newManager.phone,
    newManager.region,
    newManager.chapter,
    newManager.createdAt
  ];
  
  sheet.appendRow(row);
  
  return createResponse({ success: true, manager: newManager });
}

/**
 * 포럼 링크 생성/업데이트
 */
function createLink(data) {
  const { forumClass, linkType, url, description } = data;
  
  if (!forumClass || !linkType || !url) {
    return createResponse({ error: 'Missing required fields' }, 400);
  }
  
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.LINKS);
  
  if (!sheet) {
    return createResponse({ error: 'Links sheet not found' }, 404);
  }
  
  const linkId = generateLinkId();
  const newLink = {
    id: linkId,
    forumClass: forumClass,
    linkType: linkType,
    url: url,
    description: description || '',
    createdAt: new Date()
  };
  
  const row = [
    newLink.id,
    newLink.forumClass,
    newLink.linkType,
    newLink.url,
    newLink.description,
    newLink.createdAt
  ];
  
  sheet.appendRow(row);
  
  return createResponse({ success: true, link: newLink });
}

// 유틸리티 함수들

/**
 * 시트 데이터 조회
 */
function getSheetData(spreadsheet, sheetName) {
  const sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) return [];
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rows = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = {};
    headers.forEach((header, index) => {
      row[header] = data[i][index];
    });
    rows.push(row);
  }
  
  return rows;
}

/**
 * 사용자 찾기
 */
function findUser(region, chapter, email, pin, className) {
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.USERS);
  
  if (!sheet) return null;
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[1] === region && row[2] === chapter && row[3] === email && 
        row[4] === pin && row[5] === className) {
      const user = {};
      headers.forEach((header, index) => {
        user[header] = row[index];
      });
      return user;
    }
  }
  
  return null;
}

/**
 * ID로 사용자 조회
 */
function getUserById(userId) {
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.USERS);
  
  if (!sheet) return null;
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[0] === userId) {
      const user = {};
      headers.forEach((header, index) => {
        user[header] = row[index];
      });
      return user;
    }
  }
  
  return null;
}

/**
 * 사용자별 출석 기록 조회
 */
function getAttendanceByUserId(userId) {
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  const sheet = spreadsheet.getSheetByName(SHEET_NAMES.ATTENDANCE);
  
  if (!sheet) return [];
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const attendance = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[0] === userId) {
      const record = {};
      headers.forEach((header, index) => {
        record[header] = row[index];
      });
      attendance.push(record);
    }
  }
  
  return attendance;
}

/**
 * ID 생성 함수들
 */
function generateUserId() {
  return 'U' + String(Date.now()).slice(-6);
}

function generateSessionId() {
  return 'S' + String(Date.now()).slice(-6);
}

function generateManagerId() {
  return 'M' + String(Date.now()).slice(-6);
}

function generateLinkId() {
  return 'L' + String(Date.now()).slice(-6);
}

/**
 * 응답 생성
 */
function createResponse(data, statusCode = 200) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON)
    .setStatusCode(statusCode);
}

/**
 * 시트 초기화 (최초 설정 시 사용)
 */
function initializeSheets() {
  const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
  
  // Users 시트 생성
  createSheetIfNotExists(spreadsheet, SHEET_NAMES.USERS, [
    'id', 'region', 'chapter', 'email', 'pin', 'className', 'name', 'createdAt', 'stamps'
  ]);
  
  // Sessions 시트 생성
  createSheetIfNotExists(spreadsheet, SHEET_NAMES.SESSIONS, [
    'id', 'title', 'date', 'time', 'type', 'location', 'onlineLink', 'className', 'managerId', 'createdAt'
  ]);
  
  // Attendance 시트 생성
  createSheetIfNotExists(spreadsheet, SHEET_NAMES.ATTENDANCE, [
    'userId', 'sessionId', 'attended', 'timestamp'
  ]);
  
  // Managers 시트 생성
  createSheetIfNotExists(spreadsheet, SHEET_NAMES.MANAGERS, [
    'id', 'forumClass', 'name', 'email', 'phone', 'region', 'chapter', 'createdAt'
  ]);
  
  // Links 시트 생성
  createSheetIfNotExists(spreadsheet, SHEET_NAMES.LINKS, [
    'id', 'forumClass', 'linkType', 'url', 'description', 'createdAt'
  ]);
  
  console.log('Sheets initialized successfully');
}

/**
 * 시트가 없으면 생성
 */
function createSheetIfNotExists(spreadsheet, sheetName, headers) {
  let sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    
    // 헤더 스타일링
    const headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground('#4285f4');
    headerRange.setFontColor('#ffffff');
    headerRange.setFontWeight('bold');
  }
  return sheet;
}
