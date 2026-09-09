-- Seed data for a fictional feature film: "Neon Harbor"
-- Enough realistic friction for the agent to demonstrate multi-step reasoning

INSERT INTO production_memory.productions VALUES
('prod_neon_harbor', 'Neon Harbor', 'feature', 'principal', '2026-06-01', '2026-11-15', 28500000.00, now64(3));

-- Shots
INSERT INTO production_memory.shots VALUES
('shot_nh_12a', 'prod_neon_harbor', '12', 'A', 'Detective enters rain-soaked alley, spots the mark under neon sign', 'Chinatown Alley, Night', 'EXT', 'NIGHT', 'completed', 45, 52, '2026-07-14', now64(3), now64(3)),
('shot_nh_12b', 'prod_neon_harbor', '12', 'B', 'Close-up on mark lighting cigarette, rain reflecting on face', 'Chinatown Alley, Night', 'EXT', 'NIGHT', 'completed', 18, 21, '2026-07-14', now64(3), now64(3)),
('shot_nh_12c', 'prod_neon_harbor', '12', 'C', 'Detective approaches, dialogue exchange', 'Chinatown Alley, Night', 'EXT', 'NIGHT', 'completed', 38, 41, '2026-07-14', now64(3), now64(3)),
('shot_nh_18a', 'prod_neon_harbor', '18', 'A', 'Interior interrogation room, detective questions witness', 'Studio Stage 4', 'INT', 'DAY', 'in_progress', 90, NULL, '2026-08-02', now64(3), now64(3)),
('shot_nh_22a', 'prod_neon_harbor', '22', 'A', 'Rooftop chase sequence - wide establishing', 'Harbor Warehouse District', 'EXT', 'NIGHT', 'not_started', 60, NULL, NULL, now64(3), now64(3)),
('shot_nh_22b', 'prod_neon_harbor', '22', 'B', 'Hand-to-hand fight on rooftop edge', 'Harbor Warehouse District', 'EXT', 'NIGHT', 'not_started', 75, NULL, NULL, now64(3), now64(3)),
('shot_nh_29a', 'prod_neon_harbor', '29', 'A', 'Flashback - younger detective in academy', 'Police Academy Lot', 'EXT', 'DAY', 'needs_pickup', 40, 38, '2026-07-28', now64(3), now64(3));

-- Assets
INSERT INTO production_memory.assets VALUES
('asset_coat_01', 'prod_neon_harbor', 'wardrobe', 'Detective Trench Coat - Primary', 'Charcoal trench, weathered, specific scuff on left elbow', 3, 'in_use', 'Wardrobe Trailer A', 'shot_nh_12c', now64(3), now64(3)),
('asset_coat_01_v2', 'prod_neon_harbor', 'wardrobe', 'Detective Trench Coat - Backup', 'Identical backup coat, cleaner condition', 1, 'available', 'Wardrobe Trailer A', NULL, now64(3), now64(3)),
('asset_watch_01', 'prod_neon_harbor', 'prop', 'Vintage Rolex Explorer', 'Hero prop watch, stopped at 10:17', 2, 'in_use', 'Prop Truck', 'shot_nh_12b', now64(3), now64(3)),
('asset_cigarette_case', 'prod_neon_harbor', 'prop', 'Silver Cigarette Case', 'Engraved case used by the mark', 1, 'available', 'Prop Truck', 'shot_nh_12b', now64(3), now64(3)),
('asset_neon_sign', 'prod_neon_harbor', 'set', 'Neon "Harbor Lights" Sign', 'Practical neon sign for alley scenes', 1, 'available', 'Set Storage', 'shot_nh_12a', now64(3), now64(3)),
('asset_vfx_rain', 'prod_neon_harbor', 'vfx', 'Digital Rain Augmentation Plate', 'CG rain layers for alley sequence', 4, 'in_use', 'VFX Vendor: PixelForge', 'shot_nh_12a', now64(3), now64(3));

-- Continuity notes (the interesting ones)
INSERT INTO production_memory.continuity_notes VALUES
('note_001', 'prod_neon_harbor', 'shot_nh_12a', 'wardrobe', 'warning',
 'In 12A the detective''s coat shows a clear scuff on the left elbow. In 12B the scuff is missing (clean coat used). Must match for the sequence.',
 'asset_coat_01', 'Script Supervisor - Maya R.', 0, NULL, '2026-07-14 23:40:00', NULL),

('note_002', 'prod_neon_harbor', 'shot_nh_12b', 'prop', 'critical',
 'Hero watch is stopped at 10:17 in this close-up. Later dialogue in scene 18 references "just after midnight". Timeline inconsistency.',
 'asset_watch_01', 'Script Supervisor - Maya R.', 0, NULL, '2026-07-14 23:55:00', NULL),

('note_003', 'prod_neon_harbor', 'shot_nh_12c', 'action', 'info',
 'Detective enters from frame left in 12A/12B but from frame right in 12C. Possible geography issue depending on coverage.',
 NULL, 'Script Supervisor - Maya R.', 0, NULL, '2026-07-15 00:10:00', NULL),

('note_004', 'prod_neon_harbor', 'shot_nh_29a', 'makeup', 'warning',
 'Flashback makeup aging is inconsistent with the younger timeline established in the director''s treatment. Needs review before pickup.',
 NULL, 'Makeup Continuity - Lena K.', 0, NULL, '2026-07-28 18:20:00', NULL),

('note_005', 'prod_neon_harbor', 'shot_nh_18a', 'wardrobe', 'critical',
 'Interrogation scene currently shooting. Detective is wearing the clean backup coat. If we cut to the alley sequence the scuff will jump.',
 'asset_coat_01_v2', '1st AD - Jordan T.', 0, NULL, '2026-08-02 11:15:00', NULL);

-- Schedule
INSERT INTO production_memory.schedule_events VALUES
('evt_001', 'prod_neon_harbor', 'shoot', 'Alley Sequence (Scene 12)', 'Chinatown Alley Night Exterior', '2026-07-14 20:00:00', '2026-07-15 04:00:00', '1st Unit', 'completed', 'Rain machine + practical neon', now64(3)),
('evt_002', 'prod_neon_harbor', 'shoot', 'Interrogation (Scene 18)', 'Studio Stage 4', '2026-08-02 08:00:00', '2026-08-02 18:00:00', '1st Unit', 'in_progress', 'Talent: lead + guest star', now64(3)),
('evt_003', 'prod_neon_harbor', 'shoot', 'Rooftop Chase (Scene 22)', 'Harbor Warehouse District', '2026-08-12 19:00:00', '2026-08-13 05:00:00', '1st Unit', 'scheduled', 'Stunt coordinator required, high risk', now64(3)),
('evt_004', 'prod_neon_harbor', 'pickup', 'Academy Flashback Pickup (29A)', 'Police Academy Lot', '2026-08-20 09:00:00', '2026-08-20 14:00:00', '2nd Unit', 'scheduled', 'Makeup continuity review first', now64(3));

-- Cost events (showing burn)
INSERT INTO production_memory.cost_events VALUES
('cost_001', 'prod_neon_harbor', 'locations', 185000.00, 'Chinatown alley night buyout + permits + rain effects', 'shot_nh_12a', '2026-07-14 00:00:00', now64(3)),
('cost_002', 'prod_neon_harbor', 'vfx', 92000.00, 'Digital rain augmentation + neon enhancement - first pass', 'shot_nh_12a', '2026-07-20 00:00:00', now64(3)),
('cost_003', 'prod_neon_harbor', 'vfx', 45000.00, 'Additional rain density + reflection work', 'shot_nh_12a', '2026-07-28 00:00:00', now64(3)),
('cost_004', 'prod_neon_harbor', 'talent', 125000.00, 'Guest star (the mark) - 2 day guarantee', NULL, '2026-07-13 00:00:00', now64(3)),
('cost_005', 'prod_neon_harbor', 'crew', 78000.00, 'Night premium + overtime for alley sequence', NULL, '2026-07-15 00:00:00', now64(3)),
('cost_006', 'prod_neon_harbor', 'vfx', 210000.00, 'Rooftop sequence previz + initial asset build (not yet shot)', 'shot_nh_22a', '2026-07-30 00:00:00', now64(3));
