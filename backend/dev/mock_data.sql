PRAGMA foreign_keys = ON;

BEGIN;

INSERT INTO brands (id, name, website, notes, archived_at, created_at, updated_at) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Northstar Beauty', 'https://northstar.example', 'Skincare and daily beauty client.', NULL, '2026-04-01 10:00:00', '2026-04-20 10:00:00'),
  ('11111111-1111-1111-1111-111111111112', 'TrailForge Gear', 'https://trailforge.example', 'Outdoor gear and creator trips.', NULL, '2026-04-02 10:00:00', '2026-04-21 10:00:00'),
  ('11111111-1111-1111-1111-111111111113', 'ByteBloom Studio', 'https://bytebloom.example', 'Consumer tech launch partner.', NULL, '2026-04-03 10:00:00', '2026-04-22 10:00:00'),
  ('11111111-1111-1111-1111-111111111114', 'Archived Snacks Co', 'https://archived-snacks.example', 'Archived brand for filter testing.', '2026-04-18 10:00:00', '2026-04-04 10:00:00', '2026-04-18 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  name = excluded.name,
  website = excluded.website,
  notes = excluded.notes,
  archived_at = excluded.archived_at,
  updated_at = excluded.updated_at;

INSERT INTO campaigns (id, name, brief, budget, start_date, end_date, status, notes, archived_at, created_at, updated_at) VALUES
  ('22222222-2222-2222-2222-222222222221', 'Spring Skincare Launch', 'Launch Northstar Beauty serum with education-first creator content.', 75000.00, '2026-05-01', '2026-06-15', 'ACTIVE', 'Priority campaign for frontend testing.', NULL, '2026-04-05 09:00:00', '2026-04-27 16:00:00'),
  ('22222222-2222-2222-2222-222222222222', 'Trail Summer Kit', 'Seed the new ultralight hiking kit with outdoor creators.', 42000.00, '2026-06-01', '2026-07-31', 'PLANNING', 'Needs shortlist review.', NULL, '2026-04-06 09:00:00', '2026-04-26 15:00:00'),
  ('22222222-2222-2222-2222-222222222223', 'Creator Tech Desk', 'Evaluate desk setup creators for ByteBloom product release.', 56000.00, '2026-04-15', '2026-05-30', 'EVALUATING', 'Testing evaluation state.', NULL, '2026-04-07 09:00:00', '2026-04-25 14:00:00'),
  ('22222222-2222-2222-2222-222222222224', 'Holiday Recap', 'Closed holiday campaign retained for historical views.', 31000.00, '2025-11-01', '2025-12-31', 'CLOSED', 'Closed campaign with completed rows.', NULL, '2025-10-01 09:00:00', '2026-01-10 14:00:00'),
  ('22222222-2222-2222-2222-222222222225', 'Archived Campaign', 'Archived campaign for include archived testing.', 15000.00, '2025-08-01', '2025-08-31', 'CLOSED', 'Archived campaign.', '2026-02-01 10:00:00', '2025-07-01 09:00:00', '2026-02-01 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  name = excluded.name,
  brief = excluded.brief,
  budget = excluded.budget,
  start_date = excluded.start_date,
  end_date = excluded.end_date,
  status = excluded.status,
  notes = excluded.notes,
  archived_at = excluded.archived_at,
  updated_at = excluded.updated_at;

INSERT INTO campaign_brands (id, campaign_id, brand_id, role, notes, created_at, updated_at) VALUES
  ('33333333-3333-3333-3333-333333333331', '22222222-2222-2222-2222-222222222221', '11111111-1111-1111-1111-111111111111', 'lead', 'Primary campaign brand.', '2026-04-05 09:10:00', '2026-04-20 10:00:00'),
  ('33333333-3333-3333-3333-333333333332', '22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111112', 'lead', 'Outdoor brand owner.', '2026-04-06 09:10:00', '2026-04-21 10:00:00'),
  ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111113', 'lead', 'Tech launch owner.', '2026-04-07 09:10:00', '2026-04-22 10:00:00'),
  ('33333333-3333-3333-3333-333333333334', '22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111111', 'collab', 'Co-branded desk content test.', '2026-04-07 09:15:00', '2026-04-22 10:10:00'),
  ('33333333-3333-3333-3333-333333333335', '22222222-2222-2222-2222-222222222225', '11111111-1111-1111-1111-111111111114', 'legacy', 'Archived association.', '2025-07-01 09:10:00', '2026-02-01 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  campaign_id = excluded.campaign_id,
  brand_id = excluded.brand_id,
  role = excluded.role,
  notes = excluded.notes,
  updated_at = excluded.updated_at;

INSERT INTO influencers (id, display_name, full_name, gender, country, city, bio, notes, archived_at, created_at, updated_at) VALUES
  ('44444444-4444-4444-4444-444444444441', 'Maya Chen', 'Maya Chen', 'female', 'United States', 'Los Angeles', 'Beauty creator focused on sensitive skin routines.', 'Strong fit for serum education.', NULL, '2026-04-08 08:00:00', '2026-04-27 13:00:00'),
  ('44444444-4444-4444-4444-444444444442', 'Riley Brooks', 'Riley Brooks', 'nonbinary', 'United States', 'Denver', 'Outdoor creator with hiking and camping reviews.', 'Manager-led negotiations.', NULL, '2026-04-08 08:10:00', '2026-04-26 13:00:00'),
  ('44444444-4444-4444-4444-444444444443', 'Sofia Mendes', 'Sofia Mendes', 'female', 'Brazil', 'Sao Paulo', 'Lifestyle creator with beauty and wellness content.', 'Portuguese and English captions.', NULL, '2026-04-08 08:20:00', '2026-04-25 13:00:00'),
  ('44444444-4444-4444-4444-444444444444', 'Noah Patel', 'Noah Patel', 'male', 'United Kingdom', 'London', 'Desk setup and consumer tech reviewer.', 'Good technical demos.', NULL, '2026-04-08 08:30:00', '2026-04-24 13:00:00'),
  ('44444444-4444-4444-4444-444444444445', 'Avery Stone', 'Avery Stone', 'female', 'Canada', 'Vancouver', 'Adventure travel creator with strong video performance.', 'Travel reimbursement likely.', NULL, '2026-04-08 08:40:00', '2026-04-23 13:00:00'),
  ('44444444-4444-4444-4444-444444444446', 'Kenji Tanaka', 'Kenji Tanaka', 'male', 'Japan', 'Tokyo', 'Minimal desk and productivity creator.', 'High YouTube intent.', NULL, '2026-04-08 08:50:00', '2026-04-22 13:00:00'),
  ('44444444-4444-4444-4444-444444444447', 'Lina Park', 'Lina Park', 'female', 'South Korea', 'Seoul', 'Skincare and K-beauty creator.', 'Potential duplicate import checks.', NULL, '2026-04-08 09:00:00', '2026-04-21 13:00:00'),
  ('44444444-4444-4444-4444-444444444448', 'Archived Creator', 'Archived Creator', 'unknown', 'United States', 'Austin', 'Archived creator retained for filters.', 'Archived influencer.', '2026-03-01 10:00:00', '2026-01-08 09:00:00', '2026-03-01 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  display_name = excluded.display_name,
  full_name = excluded.full_name,
  gender = excluded.gender,
  country = excluded.country,
  city = excluded.city,
  bio = excluded.bio,
  notes = excluded.notes,
  archived_at = excluded.archived_at,
  updated_at = excluded.updated_at;

INSERT INTO influencer_platforms (
  id, influencer_id, platform, username, normalized_username, profile_url, normalized_profile_url,
  follower_count, engagement_rate, follower_credibility, notable_follower_rate, avg_likes,
  avg_views, avg_comments, avg_reels_plays, total_likes, total_posts_or_videos, total_views,
  bio, raw_metrics_json, last_imported_at, created_at, updated_at
) VALUES
  ('55555555-5555-5555-5555-555555555551', '44444444-4444-4444-4444-444444444441', 'instagram', 'maya.glow', 'maya.glow', 'https://www.instagram.com/maya.glow', 'https://instagram.com/maya.glow', 245000, 0.041200, 0.892000, 0.231000, 8300, 124000, 214, 98000, 4200000, 620, 5100000, 'Sensitive skin routines and product education.', json('{"source":"mock","tier":"macro"}'), '2026-04-20 12:00:00', '2026-04-08 08:01:00', '2026-04-27 13:00:00'),
  ('55555555-5555-5555-5555-555555555552', '44444444-4444-4444-4444-444444444441', 'tiktok', 'mayaglow', 'mayaglow', 'https://www.tiktok.com/@mayaglow', 'https://tiktok.com/@mayaglow', 380000, 0.052500, 0.861000, 0.178000, 15400, 210000, 311, NULL, 6200000, 410, 8400000, 'Fast routine clips and ingredient explainers.', json('{"source":"mock","tier":"macro"}'), '2026-04-20 12:00:00', '2026-04-08 08:02:00', '2026-04-27 13:00:00'),
  ('55555555-5555-5555-5555-555555555553', '44444444-4444-4444-4444-444444444442', 'instagram', 'rileyoutside', 'rileyoutside', 'https://www.instagram.com/rileyoutside', 'https://instagram.com/rileyoutside', 118000, 0.036000, 0.804000, 0.120000, 3900, 71000, 96, 51000, 1800000, 530, 2600000, 'Hiking kit tests and camp cooking.', json('{"source":"mock","niche":"outdoor"}'), '2026-04-19 12:00:00', '2026-04-08 08:11:00', '2026-04-26 13:00:00'),
  ('55555555-5555-5555-5555-555555555554', '44444444-4444-4444-4444-444444444442', 'youtube', 'RileyOutside', 'rileyoutside', 'https://www.youtube.com/@RileyOutside', 'https://youtube.com/@rileyoutside', 76000, 0.028000, 0.835000, 0.091000, 1800, 64000, 154, NULL, 920000, 82, 5300000, 'Long-form gear reviews.', json('{"source":"mock","format":"longform"}'), '2026-04-19 12:00:00', '2026-04-08 08:12:00', '2026-04-26 13:00:00'),
  ('55555555-5555-5555-5555-555555555555', '44444444-4444-4444-4444-444444444443', 'instagram', 'sofia.moves', 'sofia.moves', 'https://www.instagram.com/sofia.moves', 'https://instagram.com/sofia.moves', 198000, 0.047000, 0.879000, 0.140000, 7200, 98000, 188, 74000, 3500000, 710, 4200000, 'Wellness, beauty, and daily routines.', json('{"source":"mock","market":"BR"}'), '2026-04-18 12:00:00', '2026-04-08 08:21:00', '2026-04-25 13:00:00'),
  ('55555555-5555-5555-5555-555555555556', '44444444-4444-4444-4444-444444444444', 'youtube', 'NoahDeskLab', 'noahdesklab', 'https://www.youtube.com/@NoahDeskLab', 'https://youtube.com/@noahdesklab', 142000, 0.031000, 0.901000, 0.201000, 2600, 97000, 301, NULL, 2100000, 148, 11200000, 'Desk technology and productivity reviews.', json('{"source":"mock","niche":"tech"}'), '2026-04-17 12:00:00', '2026-04-08 08:31:00', '2026-04-24 13:00:00'),
  ('55555555-5555-5555-5555-555555555557', '44444444-4444-4444-4444-444444444444', 'threads', 'noahdesklab', 'noahdesklab', 'https://www.threads.net/@noahdesklab', 'https://threads.net/@noahdesklab', 42000, 0.018000, 0.780000, 0.055000, 820, 12000, 43, NULL, 210000, 320, 390000, 'Desk notes and short thoughts.', json('{"source":"mock","format":"short"}'), '2026-04-17 12:00:00', '2026-04-08 08:32:00', '2026-04-24 13:00:00'),
  ('55555555-5555-5555-5555-555555555558', '44444444-4444-4444-4444-444444444445', 'tiktok', 'averytreks', 'averytreks', 'https://www.tiktok.com/@averytreks', 'https://tiktok.com/@averytreks', 310000, 0.061000, 0.812000, 0.144000, 18900, 280000, 412, NULL, 7600000, 500, 12800000, 'Fast adventure travel videos.', json('{"source":"mock","niche":"travel"}'), '2026-04-16 12:00:00', '2026-04-08 08:41:00', '2026-04-23 13:00:00'),
  ('55555555-5555-5555-5555-555555555559', '44444444-4444-4444-4444-444444444446', 'youtube', 'KenjiWorkspace', 'kenjiworkspace', 'https://www.youtube.com/@KenjiWorkspace', 'https://youtube.com/@kenjiworkspace', 88000, 0.034000, 0.874000, 0.113000, 2100, 69000, 205, NULL, 980000, 104, 7200000, 'Minimal desks and productivity.', json('{"source":"mock","market":"JP"}'), '2026-04-15 12:00:00', '2026-04-08 08:51:00', '2026-04-22 13:00:00'),
  ('55555555-5555-5555-5555-55555555555a', '44444444-4444-4444-4444-444444444447', 'instagram', 'linaskinlab', 'linaskinlab', 'https://www.instagram.com/linaskinlab', 'https://instagram.com/linaskinlab', 167000, 0.045000, 0.855000, 0.151000, 6500, 88000, 173, 68000, 2900000, 580, 3600000, 'K-beauty testing and skincare diaries.', json('{"source":"mock","market":"KR"}'), '2026-04-14 12:00:00', '2026-04-08 09:01:00', '2026-04-21 13:00:00'),
  ('55555555-5555-5555-5555-55555555555b', '44444444-4444-4444-4444-444444444448', 'instagram', 'archived.creator', 'archived.creator', 'https://www.instagram.com/archived.creator', 'https://instagram.com/archived.creator', 12000, 0.021000, 0.710000, 0.020000, 240, 3000, 12, 2400, 80000, 210, 120000, 'Archived account.', json('{"source":"mock","archived":true}'), '2026-03-01 12:00:00', '2026-01-08 09:01:00', '2026-03-01 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  influencer_id = excluded.influencer_id,
  platform = excluded.platform,
  username = excluded.username,
  normalized_username = excluded.normalized_username,
  profile_url = excluded.profile_url,
  normalized_profile_url = excluded.normalized_profile_url,
  follower_count = excluded.follower_count,
  engagement_rate = excluded.engagement_rate,
  follower_credibility = excluded.follower_credibility,
  notable_follower_rate = excluded.notable_follower_rate,
  avg_likes = excluded.avg_likes,
  avg_views = excluded.avg_views,
  avg_comments = excluded.avg_comments,
  avg_reels_plays = excluded.avg_reels_plays,
  total_likes = excluded.total_likes,
  total_posts_or_videos = excluded.total_posts_or_videos,
  total_views = excluded.total_views,
  bio = excluded.bio,
  raw_metrics_json = excluded.raw_metrics_json,
  last_imported_at = excluded.last_imported_at,
  updated_at = excluded.updated_at;

INSERT INTO influencer_audience_snapshots (
  id, influencer_platform_id, source, age_gender_json, top_countries_json, top_cities_json,
  top_interests_json, captured_at, created_at
) VALUES
  ('66666666-6666-6666-6666-666666666661', '55555555-5555-5555-5555-555555555551', 'modash_csv', json('{"female_18_24":0.32,"female_25_34":0.41,"male_25_34":0.12}'), json('[{"country":"United States","share":0.62},{"country":"Canada","share":0.08}]'), json('[{"city":"Los Angeles","share":0.14},{"city":"New York","share":0.09}]'), json('[{"interest":"Beauty","share":0.73},{"interest":"Wellness","share":0.44}]'), '2026-04-20 12:00:00', '2026-04-20 12:00:00'),
  ('66666666-6666-6666-6666-666666666662', '55555555-5555-5555-5555-555555555553', 'modash_csv', json('{"female_25_34":0.28,"male_25_34":0.33,"male_35_44":0.17}'), json('[{"country":"United States","share":0.71},{"country":"Canada","share":0.12}]'), json('[{"city":"Denver","share":0.11},{"city":"Seattle","share":0.06}]'), json('[{"interest":"Outdoors","share":0.81},{"interest":"Travel","share":0.37}]'), '2026-04-19 12:00:00', '2026-04-19 12:00:00'),
  ('66666666-6666-6666-6666-666666666663', '55555555-5555-5555-5555-555555555556', 'modash_csv', json('{"male_25_34":0.43,"male_35_44":0.21,"female_25_34":0.16}'), json('[{"country":"United Kingdom","share":0.38},{"country":"United States","share":0.27}]'), json('[{"city":"London","share":0.18},{"city":"Manchester","share":0.05}]'), json('[{"interest":"Technology","share":0.69},{"interest":"Productivity","share":0.52}]'), '2026-04-17 12:00:00', '2026-04-17 12:00:00')
ON CONFLICT(id) DO UPDATE SET
  influencer_platform_id = excluded.influencer_platform_id,
  source = excluded.source,
  age_gender_json = excluded.age_gender_json,
  top_countries_json = excluded.top_countries_json,
  top_cities_json = excluded.top_cities_json,
  top_interests_json = excluded.top_interests_json,
  captured_at = excluded.captured_at;

INSERT INTO influencer_contacts (id, influencer_id, name, email, role, is_primary, source, notes, created_at, updated_at) VALUES
  ('77777777-7777-7777-7777-777777777771', '44444444-4444-4444-4444-444444444441', 'Maya Chen', 'maya@example.com', 'creator', 1, 'mock', 'Direct creator email.', '2026-04-08 08:03:00', '2026-04-27 13:00:00'),
  ('77777777-7777-7777-7777-777777777772', '44444444-4444-4444-4444-444444444442', 'Sam Manager', 'sam.manager@example.com', 'manager', 1, 'mock', 'Represents Riley and Avery.', '2026-04-08 08:13:00', '2026-04-26 13:00:00'),
  ('77777777-7777-7777-7777-777777777773', '44444444-4444-4444-4444-444444444443', 'Sofia Mendes', 'sofia@example.com', 'creator', 1, 'mock', 'Direct creator email.', '2026-04-08 08:23:00', '2026-04-25 13:00:00'),
  ('77777777-7777-7777-7777-777777777774', '44444444-4444-4444-4444-444444444444', 'Noah Patel', 'noah@example.com', 'creator', 1, 'mock', 'Direct creator email.', '2026-04-08 08:33:00', '2026-04-24 13:00:00'),
  ('77777777-7777-7777-7777-777777777775', '44444444-4444-4444-4444-444444444445', 'Sam Manager', 'sam.manager@example.com', 'manager', 1, 'mock', 'Same manager as Riley.', '2026-04-08 08:43:00', '2026-04-23 13:00:00'),
  ('77777777-7777-7777-7777-777777777776', '44444444-4444-4444-4444-444444444446', 'Kenji Tanaka', 'kenji@example.com', 'creator', 1, 'mock', 'Direct creator email.', '2026-04-08 08:53:00', '2026-04-22 13:00:00'),
  ('77777777-7777-7777-7777-777777777777', '44444444-4444-4444-4444-444444444447', 'Lina Park', 'lina@example.com', 'creator', 1, 'mock', 'Direct creator email.', '2026-04-08 09:03:00', '2026-04-21 13:00:00')
ON CONFLICT(id) DO UPDATE SET
  influencer_id = excluded.influencer_id,
  name = excluded.name,
  email = excluded.email,
  role = excluded.role,
  is_primary = excluded.is_primary,
  source = excluded.source,
  notes = excluded.notes,
  updated_at = excluded.updated_at;

INSERT INTO stored_files (id, kind, original_name, storage_path, mime_type, size_bytes, checksum, created_at, updated_at) VALUES
  ('88888888-8888-8888-8888-888888888881', 'import_source', 'mock-modash-export.csv', 'mock/imports/mock-modash-export.csv', 'text/csv', 141776, 'mock-import-checksum', '2026-04-20 12:00:00', '2026-04-20 12:00:00'),
  ('88888888-8888-8888-8888-888888888882', 'campaign_export', 'spring-skincare-export.csv', 'mock/exports/spring-skincare-export.csv', 'text/csv', 4096, 'mock-export-checksum', '2026-04-27 12:00:00', '2026-04-27 12:00:00'),
  ('88888888-8888-8888-8888-888888888883', 'receipt', 'hotel-receipt.pdf', 'mock/receipts/hotel-receipt.pdf', 'application/pdf', 204800, 'mock-receipt-checksum', '2026-04-22 12:00:00', '2026-04-22 12:00:00')
ON CONFLICT(id) DO UPDATE SET
  kind = excluded.kind,
  original_name = excluded.original_name,
  storage_path = excluded.storage_path,
  mime_type = excluded.mime_type,
  size_bytes = excluded.size_bytes,
  checksum = excluded.checksum,
  updated_at = excluded.updated_at;

INSERT INTO deals (id, campaign_id, influencer_id, status, lost_reason, labels_json, internal_notes, source_list_status, archived_at, created_at, updated_at) VALUES
  ('99999999-9999-9999-9999-999999999991', '22222222-2222-2222-2222-222222222221', '44444444-4444-4444-4444-444444444441', 'ACTIVE', NULL, json('["priority","beauty","contracted"]'), 'Serum integration confirmed.', 'Imported from Modash', NULL, '2026-04-10 09:00:00', '2026-04-27 12:00:00'),
  ('99999999-9999-9999-9999-999999999992', '22222222-2222-2222-2222-222222222221', '44444444-4444-4444-4444-444444444443', 'NEGOTIATING', NULL, json('["beauty","LATAM"]'), 'Negotiating usage rights.', 'Manual shortlist', NULL, '2026-04-10 09:05:00', '2026-04-26 12:00:00'),
  ('99999999-9999-9999-9999-999999999993', '22222222-2222-2222-2222-222222222221', '44444444-4444-4444-4444-444444444447', 'OUTREACHED', NULL, json('["k-beauty","follow-up"]'), 'Initial outreach sent.', 'Imported from Modash', NULL, '2026-04-10 09:10:00', '2026-04-25 12:00:00'),
  ('99999999-9999-9999-9999-999999999994', '22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444442', 'APPROVED', NULL, json('["outdoor","manager"]'), 'Approved for kit seeding.', 'Manual shortlist', NULL, '2026-04-11 09:00:00', '2026-04-24 12:00:00'),
  ('99999999-9999-9999-9999-999999999995', '22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444445', 'RESPONDED', NULL, json('["travel","reimbursement"]'), 'Manager asked for travel terms.', 'Manual shortlist', NULL, '2026-04-11 09:05:00', '2026-04-23 12:00:00'),
  ('99999999-9999-9999-9999-999999999996', '22222222-2222-2222-2222-222222222223', '44444444-4444-4444-4444-444444444444', 'DRAFT', NULL, json('["tech","desk"]'), 'Needs technical review.', 'Research list', NULL, '2026-04-12 09:00:00', '2026-04-22 12:00:00'),
  ('99999999-9999-9999-9999-999999999997', '22222222-2222-2222-2222-222222222223', '44444444-4444-4444-4444-444444444446', 'LOST', 'Rate too high', json('["tech","youtube"]'), 'Pass for MVP budget.', 'Research list', NULL, '2026-04-12 09:05:00', '2026-04-21 12:00:00'),
  ('99999999-9999-9999-9999-999999999998', '22222222-2222-2222-2222-222222222224', '44444444-4444-4444-4444-444444444441', 'COMPLETED', NULL, json('["holiday","completed"]'), 'Completed and reported.', 'Legacy campaign', NULL, '2025-11-05 09:00:00', '2026-01-10 12:00:00'),
  ('99999999-9999-9999-9999-999999999999', '22222222-2222-2222-2222-222222222224', '44444444-4444-4444-4444-444444444443', 'COMPLETED', NULL, json('["holiday","archived-row"]'), 'Archived deal row for filters.', 'Legacy campaign', '2026-01-15 12:00:00', '2025-11-05 09:05:00', '2026-01-15 12:00:00')
ON CONFLICT(id) DO UPDATE SET
  campaign_id = excluded.campaign_id,
  influencer_id = excluded.influencer_id,
  status = excluded.status,
  lost_reason = excluded.lost_reason,
  labels_json = excluded.labels_json,
  internal_notes = excluded.internal_notes,
  source_list_status = excluded.source_list_status,
  archived_at = excluded.archived_at,
  updated_at = excluded.updated_at;

INSERT INTO deliverables (id, deal_id, type, quantity, due_date, status, published_url, notes, created_at, updated_at) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1', '99999999-9999-9999-9999-999999999991', 'Instagram Reel', 1, '2026-05-12', 'IN_PROGRESS', NULL, 'Ingredient education angle.', '2026-04-15 10:00:00', '2026-04-27 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2', '99999999-9999-9999-9999-999999999991', 'Instagram Story Set', 3, '2026-05-14', 'TODO', NULL, 'Include swipe link.', '2026-04-15 10:05:00', '2026-04-27 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3', '99999999-9999-9999-9999-999999999992', 'Instagram Reel', 1, '2026-05-20', 'TODO', NULL, 'Pending rate lock.', '2026-04-16 10:00:00', '2026-04-26 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4', '99999999-9999-9999-9999-999999999993', 'Static Post', 1, '2026-05-22', 'TODO', NULL, 'Outreach not yet accepted.', '2026-04-17 10:00:00', '2026-04-25 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5', '99999999-9999-9999-9999-999999999994', 'YouTube Integration', 1, '2026-06-18', 'TODO', NULL, 'Gear review segment.', '2026-04-18 10:00:00', '2026-04-24 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6', '99999999-9999-9999-9999-999999999995', 'TikTok Video', 2, '2026-06-25', 'SUBMITTED', NULL, 'Awaiting client review.', '2026-04-19 10:00:00', '2026-04-23 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7', '99999999-9999-9999-9999-999999999998', 'Instagram Reel', 1, '2025-12-05', 'COMPLETED', 'https://instagram.com/reel/mockholiday', 'Legacy completed post.', '2025-11-10 10:00:00', '2026-01-10 10:00:00'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa8', '99999999-9999-9999-9999-999999999998', 'Usage Report', 1, '2025-12-20', 'POSTED', 'https://reports.example/holiday', 'Posted report link.', '2025-11-10 10:05:00', '2026-01-10 10:00:00')
ON CONFLICT(id) DO UPDATE SET
  deal_id = excluded.deal_id,
  type = excluded.type,
  quantity = excluded.quantity,
  due_date = excluded.due_date,
  status = excluded.status,
  published_url = excluded.published_url,
  notes = excluded.notes,
  updated_at = excluded.updated_at;

INSERT INTO compensation_items (id, deal_id, type, description, amount, currency, recipient_name, status, due_date, completed_at, receipt_file_id, notes, created_at, updated_at) VALUES
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1', '99999999-9999-9999-9999-999999999991', 'CASH_STIPEND', 'Serum launch fee', 8500.00, 'USD', 'Maya Chen', 'PROMISED', '2026-05-01', NULL, NULL, 'Paid after final approval.', '2026-04-15 11:00:00', '2026-04-27 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2', '99999999-9999-9999-9999-999999999991', 'SAMPLE_PRODUCT', 'Serum kit and moisturizer', NULL, NULL, 'Maya Chen', 'COMPLETED', '2026-04-25', '2026-04-25 15:00:00', NULL, 'Shipment delivered.', '2026-04-15 11:05:00', '2026-04-25 15:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3', '99999999-9999-9999-9999-999999999992', 'CASH_STIPEND', 'Negotiated package', 6200.00, 'USD', 'Sofia Mendes', 'PLANNED', '2026-05-10', NULL, NULL, 'Pending rights discussion.', '2026-04-16 11:00:00', '2026-04-26 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb4', '99999999-9999-9999-9999-999999999994', 'PRODUCT_GIFT', 'Trail Summer Kit', NULL, NULL, 'Riley Brooks', 'PROMISED', '2026-05-20', NULL, NULL, 'Gifted gear kit.', '2026-04-18 11:00:00', '2026-04-24 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb5', '99999999-9999-9999-9999-999999999995', 'HOTEL_REIMBURSEMENT', 'Two-night trail lodge', 780.00, 'USD', 'Avery Stone', 'IN_PROGRESS', '2026-06-10', NULL, '88888888-8888-8888-8888-888888888883', 'Receipt expected after trip.', '2026-04-19 11:00:00', '2026-04-23 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb6', '99999999-9999-9999-9999-999999999995', 'MEAL_OR_PER_DIEM', 'Per diem', 180.00, 'USD', 'Avery Stone', 'PLANNED', '2026-06-10', NULL, NULL, 'Estimate for field shoot.', '2026-04-19 11:05:00', '2026-04-23 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb7', '99999999-9999-9999-9999-999999999997', 'CASH_STIPEND', 'Quoted fee', 12000.00, 'USD', 'Kenji Tanaka', 'CANCELLED', '2026-04-30', NULL, NULL, 'Cancelled after lost decision.', '2026-04-20 11:00:00', '2026-04-21 11:00:00'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb8', '99999999-9999-9999-9999-999999999998', 'CASH_STIPEND', 'Holiday campaign fee', 5000.00, 'USD', 'Maya Chen', 'COMPLETED', '2025-12-15', '2025-12-15 15:00:00', NULL, 'Paid.', '2025-11-10 11:00:00', '2026-01-10 11:00:00')
ON CONFLICT(id) DO UPDATE SET
  deal_id = excluded.deal_id,
  type = excluded.type,
  description = excluded.description,
  amount = excluded.amount,
  currency = excluded.currency,
  recipient_name = excluded.recipient_name,
  status = excluded.status,
  due_date = excluded.due_date,
  completed_at = excluded.completed_at,
  receipt_file_id = excluded.receipt_file_id,
  notes = excluded.notes,
  updated_at = excluded.updated_at;

INSERT INTO email_accounts (id, provider, email, display_name, sync_status, last_synced_at, created_at, updated_at) VALUES
  ('cccccccc-cccc-cccc-cccc-ccccccccccc1', 'gmail', 'agency@example.com', 'Agency Shared Inbox', 'idle', '2026-04-27 09:00:00', '2026-04-01 09:00:00', '2026-04-27 09:00:00')
ON CONFLICT(id) DO UPDATE SET
  provider = excluded.provider,
  email = excluded.email,
  display_name = excluded.display_name,
  sync_status = excluded.sync_status,
  last_synced_at = excluded.last_synced_at,
  updated_at = excluded.updated_at;

INSERT INTO email_thread_metadata (id, provider, external_thread_id, account_id, subject, participants_json, last_message_at, snippet, message_count, created_at, updated_at) VALUES
  ('dddddddd-dddd-dddd-dddd-ddddddddddd1', 'gmail', 'thread-maya-serum', 'cccccccc-cccc-cccc-cccc-ccccccccccc1', 'Spring serum launch details', json('[{"email":"maya@example.com","name":"Maya Chen"},{"email":"agency@example.com","name":"Agency"}]'), '2026-04-27 09:30:00', 'Maya confirmed the serum integration timeline.', 6, '2026-04-20 09:00:00', '2026-04-27 09:30:00'),
  ('dddddddd-dddd-dddd-dddd-ddddddddddd2', 'gmail', 'thread-riley-kit', 'cccccccc-cccc-cccc-cccc-ccccccccccc1', 'Trail kit scope', json('[{"email":"sam.manager@example.com","name":"Sam Manager"},{"email":"agency@example.com","name":"Agency"}]'), '2026-04-24 09:30:00', 'Sam asked for gear shipment timing.', 4, '2026-04-18 09:00:00', '2026-04-24 09:30:00'),
  ('dddddddd-dddd-dddd-dddd-ddddddddddd3', 'gmail', 'thread-avery-travel', 'cccccccc-cccc-cccc-cccc-ccccccccccc1', 'Avery travel reimbursement', json('[{"email":"sam.manager@example.com","name":"Sam Manager"},{"email":"agency@example.com","name":"Agency"}]'), '2026-04-23 09:30:00', 'Travel reimbursement terms are being reviewed.', 5, '2026-04-19 09:00:00', '2026-04-23 09:30:00')
ON CONFLICT(id) DO UPDATE SET
  provider = excluded.provider,
  external_thread_id = excluded.external_thread_id,
  account_id = excluded.account_id,
  subject = excluded.subject,
  participants_json = excluded.participants_json,
  last_message_at = excluded.last_message_at,
  snippet = excluded.snippet,
  message_count = excluded.message_count,
  updated_at = excluded.updated_at;

INSERT INTO email_thread_links (id, provider, external_thread_id, external_message_id, influencer_id, campaign_id, deal_id, contact_id, link_type, confidence, linked_by, created_at, updated_at) VALUES
  ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1', 'gmail', 'thread-maya-serum', 'msg-maya-006', '44444444-4444-4444-4444-444444444441', '22222222-2222-2222-2222-222222222221', '99999999-9999-9999-9999-999999999991', '77777777-7777-7777-7777-777777777771', 'manual', 1.000, 'mock-seed', '2026-04-27 09:35:00', '2026-04-27 09:35:00'),
  ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2', 'gmail', 'thread-riley-kit', 'msg-riley-004', '44444444-4444-4444-4444-444444444442', '22222222-2222-2222-2222-222222222222', '99999999-9999-9999-9999-999999999994', '77777777-7777-7777-7777-777777777772', 'inferred_from_contact', 0.880, 'mock-seed', '2026-04-24 09:35:00', '2026-04-24 09:35:00'),
  ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee3', 'gmail', 'thread-avery-travel', 'msg-avery-005', '44444444-4444-4444-4444-444444444445', '22222222-2222-2222-2222-222222222222', '99999999-9999-9999-9999-999999999995', '77777777-7777-7777-7777-777777777775', 'manual', 1.000, 'mock-seed', '2026-04-23 09:35:00', '2026-04-23 09:35:00')
ON CONFLICT(id) DO UPDATE SET
  provider = excluded.provider,
  external_thread_id = excluded.external_thread_id,
  external_message_id = excluded.external_message_id,
  influencer_id = excluded.influencer_id,
  campaign_id = excluded.campaign_id,
  deal_id = excluded.deal_id,
  contact_id = excluded.contact_id,
  link_type = excluded.link_type,
  confidence = excluded.confidence,
  linked_by = excluded.linked_by,
  updated_at = excluded.updated_at;

INSERT INTO import_sessions (id, source_type, file_name, file_hash, row_count, imported_count, skipped_count, conflict_count, target_campaign_id, created_at, updated_at) VALUES
  ('ffffffff-ffff-ffff-ffff-fffffffffff1', 'modash_csv', 'mock-modash-export.csv', 'mock-import-checksum', 8, 7, 1, 0, '22222222-2222-2222-2222-222222222221', '2026-04-20 12:10:00', '2026-04-20 12:20:00')
ON CONFLICT(id) DO UPDATE SET
  source_type = excluded.source_type,
  file_name = excluded.file_name,
  file_hash = excluded.file_hash,
  row_count = excluded.row_count,
  imported_count = excluded.imported_count,
  skipped_count = excluded.skipped_count,
  conflict_count = excluded.conflict_count,
  target_campaign_id = excluded.target_campaign_id,
  updated_at = excluded.updated_at;

INSERT INTO job_records (id, type, status, progress_current, progress_total, result_json, error_code, error_message, created_at, started_at, finished_at) VALUES
  ('12121212-1212-1212-1212-121212121211', 'import.modash.preview', 'succeeded', 8, 8, json('{"rows":8,"warnings":1}'), NULL, NULL, '2026-04-20 12:00:00', '2026-04-20 12:00:01', '2026-04-20 12:00:08'),
  ('12121212-1212-1212-1212-121212121212', 'campaign.export.csv', 'succeeded', 3, 3, json('{"file_id":"88888888-8888-8888-8888-888888888882"}'), NULL, NULL, '2026-04-27 12:00:00', '2026-04-27 12:00:01', '2026-04-27 12:00:04'),
  ('12121212-1212-1212-1212-121212121213', 'email.sync', 'failed', 2, 5, NULL, 'mock_auth_expired', 'Mock failed job for error UI testing.', '2026-04-27 13:00:00', '2026-04-27 13:00:01', '2026-04-27 13:00:05'),
  ('12121212-1212-1212-1212-121212121214', 'campaign.report.refresh', 'queued', 0, 10, NULL, NULL, NULL, '2026-04-27 14:00:00', NULL, NULL)
ON CONFLICT(id) DO UPDATE SET
  type = excluded.type,
  status = excluded.status,
  progress_current = excluded.progress_current,
  progress_total = excluded.progress_total,
  result_json = excluded.result_json,
  error_code = excluded.error_code,
  error_message = excluded.error_message,
  started_at = excluded.started_at,
  finished_at = excluded.finished_at;

INSERT INTO templates (id, type, name, subject_template, body_template, description, is_archived, created_at, updated_at) VALUES
  ('13131313-1313-1313-1313-131313131311', 'OUTREACH_EMAIL', 'Warm creator outreach', 'Collaboration with {{ brand_name }}', 'Hi {{ creator_name }},\n\nWe are building a campaign for {{ brand_name }} and thought your work would be a strong fit.\n\nBest,\nAgency', 'General outreach email.', 0, '2026-04-10 12:00:00', '2026-04-27 12:00:00'),
  ('13131313-1313-1313-1313-131313131312', 'REPORT', 'Campaign summary report', '{{ campaign_name }} summary', 'Campaign: {{ campaign_name }}\nHighlights:\n- {{ highlights }}', 'Reusable campaign report outline.', 0, '2026-04-10 12:05:00', '2026-04-27 12:05:00'),
  ('13131313-1313-1313-1313-131313131313', 'BRIEF', 'Creator brief', '{{ campaign_name }} creator brief', 'Deliverables:\n{{ deliverables }}\n\nTalking points:\n{{ talking_points }}', 'Reusable creator brief.', 0, '2026-04-10 12:10:00', '2026-04-27 12:10:00'),
  ('13131313-1313-1313-1313-131313131314', 'CONTRACT', 'Contract placeholder', '{{ campaign_name }} agreement', 'Contract drafting is deferred. This template exists for future planning only.', 'Deferred contract template placeholder.', 0, '2026-04-10 12:15:00', '2026-04-27 12:15:00')
ON CONFLICT(id) DO UPDATE SET
  type = excluded.type,
  name = excluded.name,
  subject_template = excluded.subject_template,
  body_template = excluded.body_template,
  description = excluded.description,
  is_archived = excluded.is_archived,
  updated_at = excluded.updated_at;

COMMIT;
