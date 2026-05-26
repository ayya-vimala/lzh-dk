def generate_relationship_edges(
        change_tracker, relationship_dir, additional_info_dir, db
):
    relationship_file = relationship_dir / Path('new_parallels.json')

    if not change_tracker.is_any_file_new_or_changed([relationship_file]):
        return

    print('Generating Parallels')
    relationship_data = json_load(relationship_file)

    uid_matcher = get_uid_matcher(db)

    remarks_data = json_load(additional_info_dir / 'notes.json')

    remarks = defaultdict(dict)
    for remark in remarks_data:
        uids = remark['relations']
        remark_text = remark['remark']
        remarks[frozenset(uids)] = remark_text

    def process_uids(from_uid, to_uids, r_type, is_resembling, ll_edges):
        """Generate edges from one UID to a list of target UIDs."""
        m = regex.search('[0-9]+$', from_uid)
        from_nr = int(m[0]) if m else 0

        true_from_uids = uid_matcher.get_matching_uids(from_uid)
        if not true_from_uids and ' ' not in from_uid:
            logging.error(f'Relationship from uid could not be matched: {from_uid} (dropped)')
            return

        for to_uid in to_uids:
            if to_uid == from_uid:
                continue
            true_to_uids = uid_matcher.get_matching_uids(to_uid)
            if not true_to_uids:
                logging.info(f'Relationship to uid could not be matched: {to_uid} (appears as orphan)')
                true_to_uids = ['orphan']

            for true_from_uid in true_from_uids:
                for true_to_uid in true_to_uids:
                    remark = remarks.get(frozenset([true_from_uid, true_to_uid]), None)
                    ll_edges.append({
                        '_from': true_from_uid,
                        '_to': true_to_uid,
                        'from': from_uid,
                        'number': from_nr,
                        'to': to_uid.split('-')[0],
                        'type': r_type,
                        'resembling': is_resembling,
                        'remark': remark,
                    })

    def process_retell_mention(first_uid, other_uids, r_type, ll_edges):
        """Generate bidirectional edges for retells and mentions."""
        m = regex.search('[0-9]+$', first_uid)
        from_nr = int(m[0]) if m else 0

        true_first_uids = uid_matcher.get_matching_uids(first_uid)

        for true_first_uid, to_uid in product(true_first_uids, other_uids):
            true_from_uids = uid_matcher.get_matching_uids(to_uid)
            if not true_from_uids and ' ' not in to_uid:
                logging.error(f'Relationship from uid could not be matched: {to_uid} (dropped)')
                continue

            for true_from_uid in true_from_uids:
                remark = remarks.get(frozenset([true_from_uid, true_first_uid]), None)
                ll_edges.append({
                    '_from': true_first_uid,
                    '_to': true_from_uid,
                    'from': first_uid,
                    'to': to_uid,
                    'number': from_nr,
                    'type': r_type,
                    'resembling': False,
                    'remark': remark,
                })
                m = regex.search('[0-9]+$', to_uid)
                to_nr = int(m[0]) if m else 0
                ll_edges.append({
                    '_from': true_from_uid,
                    '_to': true_first_uid,
                    'from': to_uid,
                    'to': first_uid,
                    'number': to_nr,
                    'type': r_type,
                    'resembling': False,
                    'remark': remark,
                })

    ll_edges = []

    for sutta_uid, entry in tqdm(relationship_data.items()):

        # Process top-level full and resembling parallels
        full_uids = entry.get('full', [])
        resembling_uids = entry.get('resembling', [])
        all_full = full_uids + resembling_uids

        for from_uid in full_uids:
            other_full = [u for u in full_uids if u != from_uid]
            process_uids(from_uid, other_full, 'full', False, ll_edges)
            process_uids(from_uid, resembling_uids, 'full', True, ll_edges)

        for from_uid in resembling_uids:
            process_uids(from_uid, full_uids, 'full', True, ll_edges)
            other_resembling = [u for u in resembling_uids if u != from_uid]
            process_uids(from_uid, other_resembling, 'full', True, ll_edges)

        # Process top-level retells and mentions
        retell_uids = entry.get('retells', [])
        mention_uids = entry.get('mentions', [])

        if retell_uids:
            process_retell_mention(sutta_uid, retell_uids, 'retelling', ll_edges)
        if mention_uids:
            process_retell_mention(sutta_uid, mention_uids, 'mention', ll_edges)

        # Process sections
        for section_uid, section in entry.get('sections', {}).items():
            section_full = section.get('full', [])
            section_resembling = section.get('resembling', [])

            for from_uid in section_full:
                other_full = [u for u in section_full if u != from_uid]
                process_uids(from_uid, other_full, 'full', False, ll_edges)
                process_uids(from_uid, section_resembling, 'full', True, ll_edges)

            for from_uid in section_resembling:
                process_uids(from_uid, section_full, 'full', True, ll_edges)
                other_resembling = [u for u in section_resembling if u != from_uid]
                process_uids(from_uid, other_resembling, 'full', True, ll_edges)

            section_retells = section.get('retells', [])
            section_mentions = section.get('mentions', [])

            if section_retells:
                process_retell_mention(section_uid, section_retells, 'retelling', ll_edges)
            if section_mentions:
                process_retell_mention(section_uid, section_mentions, 'mention', ll_edges)

    # Chunk the import as before
    db['relationship'].truncate()
    for chunk in chunks(ll_edges, 10000):
        db['relationship'].import_bulk_logged(chunk, from_prefix='super_nav_details', to_prefix='super_nav_details')