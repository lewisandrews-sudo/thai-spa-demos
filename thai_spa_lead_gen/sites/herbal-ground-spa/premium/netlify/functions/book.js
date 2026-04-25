// thai_spa_lead_gen/templates/booking_function.js.j2
// Deployed as netlify/functions/book.js inside each premium site
const { createClient } = require('@supabase/supabase-js');
const https = require('https');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  let body;
  try { body = JSON.parse(event.body); }
  catch { return { statusCode: 400, body: 'Invalid JSON' }; }

  const { business_slug, service, booking_date, booking_time,
          customer_name, customer_phone, customer_line_id } = body;

  if (!service || !booking_date || !booking_time || !customer_name || !customer_phone) {
    return { statusCode: 400, body: 'Missing required fields' };
  }

  // Save to Supabase
  const tableName = `bookings_herbal_ground_spa`;
  const { error } = await supabase.from(tableName).insert([{
    service, booking_date, booking_time,
    customer_name, customer_phone,
    customer_line_id: customer_line_id || null,
    status: 'pending',
  }]);

  if (error) {
    console.error('Supabase error:', error);
    return { statusCode: 500, body: 'Database error' };
  }

  // Send LINE Notify
  const lineMessage =
    `📅 นัดหมายใหม่!\n` +
    `ร้าน: Herbal Ground Spa\n` +
    `บริการ: ${service}\n` +
    `วันที่: ${booking_date} เวลา ${booking_time}\n` +
    `ชื่อ: ${customer_name}\n` +
    `โทร: ${customer_phone}` +
    (customer_line_id ? `\nLINE: ${customer_line_id}` : '');

  await sendLineNotify(lineMessage, process.env.LINE_NOTIFY_TOKEN);

  return {
    statusCode: 200,
    headers: { 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify({ ok: true }),
  };
};

function sendLineNotify(message, token) {
  return new Promise((resolve) => {
    const encoded = encodeURIComponent(message);
    const postData = `message=${encoded}`;
    const req = https.request({
      hostname: 'notify-api.line.me',
      path: '/api/notify',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData),
      },
    }, resolve);
    req.on('error', resolve);
    req.write(postData);
    req.end();
  });
}